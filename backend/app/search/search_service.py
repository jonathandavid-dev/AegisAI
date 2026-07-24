import time
import structlog
from typing import Dict, Any, List
from app.retrieval.query_service import QueryService
from app.retrieval.filters import FilterService
from app.retrieval.retrieval_service import RetrievalService
from app.retrieval.ranking_service import RankingService
from app.embeddings.embedding_service import EmbeddingService
from app.cache.retrieval_cache import RetrievalCache
from app.cache.embedding_cache import EmbeddingCache
from app.observability.tracing import trace_span
from app.observability.metrics import track_search_latency, track_embedding_latency

logger = structlog.get_logger("aegis.search")

class SearchService:
    """Orchestrator coordinating query preprocessing, embedding generation, vector matching, ranking, and workspace isolation."""
    
    @staticmethod
    async def search(
        query: str, 
        workspace_id: int = 1,
        top_k: int = 10, 
        filters: Dict[str, Any] = None,
        similarity_threshold: float = 0.50
    ) -> Dict[str, Any]:
        """Runs the complete vector search retrieval pipeline restricted to a workspace's collection."""
        start_total = time.perf_counter()
        logger.info("Search Started", query=query, workspace_id=workspace_id)
        
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
                # 2. Clean query
                cleaned_query = QueryService.normalize_query(query)
                
                # 3. Generate embedding (with Embedding Cache check)
                start_embed = time.perf_counter()
                query_embedding = []
                try:
                    cached_embed = await EmbeddingCache.get(workspace_id, cleaned_query)
                    if cached_embed is not None:
                        query_embedding = cached_embed
                        logger.info("Embedding Cache Hit", text=cleaned_query[:30])
                    else:
                        query_embeddings = EmbeddingService.embed_texts([cleaned_query], batch_size=1)
                        query_embedding = query_embeddings[0] if query_embeddings else []
                        await EmbeddingCache.set(workspace_id, cleaned_query, query_embedding)
                except Exception as exc:
                    logger.error("embedding_cache_lookup_failed", error=str(exc))
                    # Fallback to direct embedding
                    query_embeddings = EmbeddingService.embed_texts([cleaned_query], batch_size=1)
                    query_embedding = query_embeddings[0] if query_embeddings else []
                    
                embed_duration = (time.perf_counter() - start_embed) * 1000.0
                logger.info("Query Embedded", duration_ms=embed_duration)
                track_embedding_latency(embed_duration / 1000.0)
                
                # 4. Process metadata filters
                compiled_where = FilterService.compile_filters(filters or {})
                
                # 5. Search vector store (scoped to workspace_<id> collection)
                start_search = time.perf_counter()
                raw_candidates = RetrievalService.retrieve_candidates(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where_filter=compiled_where,
                    collection_name=f"workspace_{workspace_id}"
                )
                search_duration = (time.perf_counter() - start_search) * 1000.0
                logger.info("Vector Search Completed", duration_ms=search_duration)
                track_search_latency(search_duration / 1000.0)
                
                # 6. Apply scores and threshold filters
                start_rank = time.perf_counter()
                ranked_results = RankingService.rank_results(
                    chroma_results=raw_candidates,
                    similarity_threshold=similarity_threshold,
                    top_k=top_k
                )
                rank_duration = (time.perf_counter() - start_rank) * 1000.0
                logger.info("Ranking Completed", duration_ms=rank_duration)
                
                total_duration = (time.perf_counter() - start_total) * 1000.0
                logger.info("Search Completed", total_duration_ms=total_duration)
                
                results_payload = {
                    "query": query,
                    "results": ranked_results,
                    "processing_time_ms": total_duration
                }
                
                # Cache the results
                try:
                    await RetrievalCache.set(workspace_id, query, top_k, filters, results_payload)
                except Exception as exc:
                    logger.error("retrieval_cache_save_failed", error=str(exc))
                    
                return results_payload
                
            except Exception as exc:
                total_duration = (time.perf_counter() - start_total) * 1000.0
                logger.error("Search Failed", error=str(exc), duration_ms=total_duration)
                raise exc
