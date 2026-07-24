from typing import Any
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.models.evaluation import BenchmarkCase, EvaluationRun
from app.evaluation.evaluation_service import EvaluationService
from app.evaluation.benchmark_service import BenchmarkService
from app.evaluation.benchmark_runner import BenchmarkRunner
from app.evaluation.regression_runner import RegressionRunner
from app.benchmarks.benchmark_loader import BenchmarkLoader
from app.tenancy.tenant_guard import WorkspacePermissionChecker
from app.tenancy.tenant_context import TenantContext

from pydantic import BaseModel

class AdhocEvalRequest(BaseModel):
    question: str
    answer: str
    expected_answer: str
    expected_keywords: list[str] = []
    retrieved_docs: list[str] = []
    expected_docs: list[str] = []
    citations: list = []
    context_chunks: list[str] = []
    retrieval_latency_ms: float = 100.0
    total_latency_ms: float = 1000.0

class BenchmarkCaseCreate(BaseModel):
    question: str
    expected_answer: str
    expected_sources: list[str] | None = None
    expected_documents: list[str] | None = None
    expected_keywords: list[str] | None = None
    category: str = "General"
    difficulty: str = "Medium"
    ground_truth: str

router = APIRouter()

@router.post("/run", status_code=status.HTTP_200_OK)
async def run_adhoc_eval(
    request: AdhocEvalRequest,
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Runs ad-hoc turn metrics calculation on a specific RAG question-answer pair.
    """
    return EvaluationService.evaluate_turn(
        question=request.question,
        generated_answer=request.answer,
        expected_answer=request.expected_answer,
        expected_keywords=request.expected_keywords,
        retrieved_docs=request.retrieved_docs,
        expected_docs=request.expected_docs,
        citations=request.citations,
        context_chunks=request.context_chunks,
        retrieval_latency_ms=request.retrieval_latency_ms,
        total_latency_ms=request.total_latency_ms
    )

@router.post("/run-suite", status_code=status.HTTP_200_OK)
async def trigger_benchmark_suite(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> Any:
    """
    Triggers complete benchmark execution across all database seeded cases, 
    calculates metrics, and evaluates regressions against historical baselines.
    """
    stmt_check = select(BenchmarkCase)
    res_check = await db.execute(stmt_check)
    if not res_check.scalars().first():
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        seed_path = os.path.join(base_dir, "datasets", "default_benchmarks.json")
        await BenchmarkLoader.seed_benchmarks(db, seed_path)

    run = await BenchmarkRunner.run_suite(
        db=db,
        workspace_id=tenant_context.workspace.id,
        account_id=current_account.id
    )

    regression_report = await RegressionRunner.compare_to_baseline(db, run)
    
    return {
        "run_id": run.id,
        "run_type": run.run_type,
        "overall_score": run.overall_score,
        "category_scores": run.category_scores,
        "results": run.results,
        "created_at": run.created_at,
        "regression": regression_report
    }

@router.get("/history", status_code=status.HTTP_200_OK)
async def get_evaluation_history(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Retrieves previous benchmark execution runs.
    """
    stmt = select(EvaluationRun).order_by(desc(EvaluationRun.id))
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [
        {
            "id": r.id,
            "run_type": r.run_type,
            "overall_score": r.overall_score,
            "category_scores": r.category_scores,
            "results": r.results,
            "baseline_run_id": r.baseline_run_id,
            "created_at": r.created_at
        }
        for r in runs
    ]

@router.get("/history/{run_id}", status_code=status.HTTP_200_OK)
async def get_evaluation_details(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Retrieves detailed breakdown of a specific historical run.
    """
    stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
    res = await db.execute(stmt)
    run = res.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return {
        "id": run.id,
        "run_type": run.run_type,
        "overall_score": run.overall_score,
        "category_scores": run.category_scores,
        "results": run.results,
        "baseline_run_id": run.baseline_run_id,
        "created_at": run.created_at
    }

@router.post("/benchmarks", status_code=status.HTTP_201_CREATED)
async def create_benchmark_case(
    request: BenchmarkCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Registers a new golden evaluation case in the benchmarks database.
    """
    new_case = await BenchmarkService.create_case(db, request)
    return {
        "id": new_case.id,
        "question": new_case.question,
        "expected_answer": new_case.expected_answer,
        "expected_sources": new_case.expected_sources,
        "expected_documents": new_case.expected_documents,
        "expected_keywords": new_case.expected_keywords,
        "category": new_case.category,
        "difficulty": new_case.difficulty,
        "ground_truth": new_case.ground_truth,
        "created_at": new_case.created_at
    }

@router.get("/benchmarks", status_code=status.HTTP_200_OK)
async def list_benchmark_cases(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Lists all golden evaluation cases registered.
    """
    cases = await BenchmarkService.list_cases(db)
    return [
        {
            "id": case.id,
            "question": case.question,
            "expected_answer": case.expected_answer,
            "expected_sources": case.expected_sources,
            "expected_documents": case.expected_documents,
            "expected_keywords": case.expected_keywords,
            "category": case.category,
            "difficulty": case.difficulty,
            "ground_truth": case.ground_truth,
            "created_at": case.created_at
        }
        for case in cases
    ]

@router.delete("/benchmarks/{case_id}", status_code=status.HTTP_200_OK)
async def delete_benchmark_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Removes a golden evaluation case.
    """
    deleted = await BenchmarkService.delete_case(db, case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Benchmark case not found")
    return {"message": "Benchmark case deleted successfully."}

@router.get("/quality/latest", status_code=status.HTTP_200_OK)
async def get_latest_quality_score(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> Any:
    """
    Retrieves the quality scores and overall score from the most recent evaluation run.
    """
    stmt = select(EvaluationRun).order_by(desc(EvaluationRun.id)).limit(1)
    res = await db.execute(stmt)
    latest_run = res.scalars().first()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No evaluation runs have been executed yet.")
    
    return {
        "run_id": latest_run.id,
        "overall_score": latest_run.overall_score,
        "category_scores": latest_run.category_scores,
        "created_at": latest_run.created_at
    }
