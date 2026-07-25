"""
SearchService — Enterprise hybrid RAG retrieval pipeline orchestrator.

Pipeline (Phase 11 upgrade):
  Query
    ↓ QueryExpander (Phase 5) — generate 3 semantic variants
    ↓ EmbeddingService.embed_queries() (Phase 3c) — BGE instruction prefix
    ↓ ChromaDB vector search × N variants (top 20 each)
    ↓ BM25Service.search() × N variants (top 20 each)
    ↓ FusionService.reciprocal_rank_fusion() — merge all results
    ↓ FusionService.deduplicate_near_dupes() — remove near-identical chunks
    ↓ RerankerService.rerank() — cross-encoder, return top 5
    ↓ Results with full retrieval diagnostics

Diagnostics returned (Phase 10):
  - embed_time_ms, vector_search_time_ms, bm25_time_ms, rerank_time_ms, total_time_ms
  - candidates_before_rerank, candidates_after_rerank
  - query_variants used
"""
import time
import structlog
from typing import Dict, Any, List, Optional

from app.retrieval.query_service import QueryService
from app.retrieval.filters import FilterService
from app.retrieval.retrieval_service import RetrievalService
from app.retrieval.ranking_service import RankingService
from app.retrieval.bm25_service import BM25Service
from app.retrieval.fusion_service import FusionService
from app.retrieval.reranker_service import RerankerService
from app.retrieval.query_expander import QueryExpander
from app.embeddings.embedding_service import EmbeddingService
from app.cache.retrieval_cache import RetrievalCache
from app.cache.embedding_cache import EmbeddingCache
from app.observability.tracing import trace_span
from app.observability.metrics import track_search_latency, track_embedding_latency

logger = structlog.get_logger("aegis.search")


class SearchService:
    """
    Orchestrates the full enterprise hybrid RAG retrieval pipeline.
    
    Replaces the previous pure-vector search with:
    - Multi-query expansion (query expander)
    - Parallel vector + BM25 retrieval
    - Reciprocal Rank Fusion
    - Near-dupe deduplication
    - Cross-encoder reranking
    - Full retrieval diagnostics payload
    """
    
    @staticmethod
    async def search(
        query: str, 
        workspace_id: int = 1,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.30,   # Lowered: reranker acts as quality gate
        use_query_expansion: bool = True,
        use_reranking: bool = True,
        candidates_k: int = 20               # Candidates fetched before reranking
    ) -> Dict[str, Any]:
        """
        Runs the complete enterprise hybrid retrieval pipeline.
        Returns results + full retrieval diagnostics.
        """
        start_total = time.perf_counter()
        logger.info("Hybrid Search Started", query=query, workspace_id=workspace_id)
        
        # 1. Check Retrieval Cache
        try:
            cached_search = await RetrievalCache.get(workspace_id, query, top_k, filters)
            if cached_search is not None:
                logger.info("Search Cache Hit", query=query, workspace_id=workspace_id)
                cached_search["processing_time_ms"] = (time.perf_counter() - start_total) * 1000.0
                return cached_search
        except Exception as exc:
            logger.error("retrieval_cache_lookup_failed", error=str(exc))
            
        with trace_span("Retrieval", {"workspace_id": workspace_id, "query": query}) as span:
            try:
                # 2. Normalize query
                cleaned_query = QueryService.normalize_query(query)
                
                # 3. Query Expansion — generate semantic variants
                start_expand = time.perf_counter()
                if use_query_expansion:
                    query_variants = await QueryExpander.expand(cleaned_query, n=3)
                else:
                    query_variants = [cleaned_query]
                expand_duration = (time.perf_counter() - start_expand) * 1000.0
                logger.info(
                    "Query Expansion Complete",
                    variants=len(query_variants),
                    duration_ms=expand_duration
                )
                
                # 4. Generate embeddings for all variants (with BGE query prefix)
                start_embed = time.perf_counter()
                query_embeddings: List[List[float]] = []
                try:
                    # Check embedding cache for original query
                    cached_embed = await EmbeddingCache.get(workspace_id, cleaned_query)
                    if cached_embed is not None:
                        logger.info("Embedding Cache Hit", text=cleaned_query[:30])
                        query_embeddings.append(cached_embed)
                        remaining_variants = query_variants[1:]  # Already have the first
                    else:
                        remaining_variants = query_variants
                    
                    if remaining_variants:
                        new_embeddings = EmbeddingService.embed_queries(
                            remaining_variants, batch_size=len(remaining_variants)
                        )
                        # Cache the first variant embedding
                        if new_embeddings:
                            await EmbeddingCache.set(workspace_id, remaining_variants[0], new_embeddings[0])
                        query_embeddings.extend(new_embeddings)
                        
                except Exception as exc:
                    logger.error("embedding_cache_lookup_failed", error=str(exc))
                    query_embeddings = EmbeddingService.embed_queries(query_variants)
                    
                embed_duration = (time.perf_counter() - start_embed) * 1000.0
                track_embedding_latency(embed_duration / 1000.0)
                logger.info("Queries Embedded", count=len(query_embeddings), duration_ms=embed_duration)
                
                # 5. Process metadata filters
                compiled_where = FilterService.compile_filters(filters or {})
                
                # 6. Vector Search — search for each query variant, collect all candidates
                start_vector = time.perf_counter()
                all_vector_results: List[List[Dict[str, Any]]] = []
                
                for i, q_embedding in enumerate(query_embeddings):
                    raw_candidates = RetrievalService.retrieve_candidates(
                        query_embedding=q_embedding,
                        top_k=candidates_k,
                        where_filter=compiled_where,
                        collection_name=f"workspace_{workspace_id}"
                    )
                    ranked = RankingService.rank_results(
                        chroma_results=raw_candidates,
                        similarity_threshold=similarity_threshold,
                        top_k=candidates_k
                    )
                    all_vector_results.append(ranked)
                
                vector_duration = (time.perf_counter() - start_vector) * 1000.0
                track_search_latency(vector_duration / 1000.0)
                total_vector_chunks = sum(len(r) for r in all_vector_results)
                logger.info(
                    "Vector Search Complete",
                    variants_searched=len(query_variants),
                    total_chunks=total_vector_chunks,
                    duration_ms=vector_duration
                )
                
                # 7. BM25 Search — keyword retrieval for each variant
                start_bm25 = time.perf_counter()
                all_bm25_results: List[List[Dict[str, Any]]] = []
                
                for variant in query_variants:
                    bm25_results = BM25Service.search(
                        query=variant,
                        workspace_id=workspace_id,
                        top_k=candidates_k
                    )
                    all_bm25_results.append(bm25_results)
                
                bm25_duration = (time.perf_counter() - start_bm25) * 1000.0
                total_bm25_chunks = sum(len(r) for r in all_bm25_results)
                logger.info(
                    "BM25 Search Complete",
                    total_chunks=total_bm25_chunks,
                    duration_ms=bm25_duration
                )
                
                # 8. Reciprocal Rank Fusion — merge all vector + BM25 result lists
                all_result_lists = all_vector_results + all_bm25_results
                fused_results = FusionService.reciprocal_rank_fusion(
                    result_lists=all_result_lists,
                    top_k=candidates_k
                )
                
                # 9. Near-duplicate deduplication
                deduped_results = FusionService.deduplicate_near_dupes(
                    results=fused_results,
                    similarity_threshold=0.90
                )
                candidates_before_rerank = len(deduped_results)
                
                # 10. Cross-encoder reranking — return only top_k
                start_rerank = time.perf_counter()
                if use_reranking and deduped_results:
                    final_results = RerankerService.rerank(
                        query=cleaned_query,
                        candidates=deduped_results,
                        top_k=top_k
                    )
                else:
                    # No reranker — just take top_k from fused results
                    final_results = deduped_results[:top_k]
                    for r in final_results:
                        r["reranker_score"] = r.get("rrf_score", r.get("score", 0.0))
                        
                rerank_duration = (time.perf_counter() - start_rerank) * 1000.0
                logger.info(
                    "Reranking Complete",
                    returned=len(final_results),
                    duration_ms=rerank_duration
                )
                
                total_duration = (time.perf_counter() - start_total) * 1000.0
                logger.info("Search Complete", total_ms=total_duration)
                
                # 11. Build full diagnostics payload
                results_payload = {
                    "query": query,
                    "results": final_results,
                    "processing_time_ms": total_duration,
                    "diagnostics": {
                        "query_variants": query_variants,
                        "embed_time_ms": round(embed_duration, 2),
                        "vector_search_time_ms": round(vector_duration, 2),
                        "bm25_time_ms": round(bm25_duration, 2),
                        "rerank_time_ms": round(rerank_duration, 2),
                        "candidates_before_rerank": candidates_before_rerank,
                        "candidates_after_rerank": len(final_results),
                        "vector_chunks_found": total_vector_chunks,
                        "bm25_chunks_found": total_bm25_chunks,
                    }
                }
                
                # Cache results
                try:
                    await RetrievalCache.set(workspace_id, query, top_k, filters, results_payload)
                except Exception as exc:
                    logger.error("retrieval_cache_save_failed", error=str(exc))
                    
                return results_payload
                
            except Exception as exc:
                total_duration = (time.perf_counter() - start_total) * 1000.0
                logger.error("Search Failed", error=str(exc), duration_ms=total_duration)
                raise exc
