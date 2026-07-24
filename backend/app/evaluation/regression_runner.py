from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.evaluation import EvaluationRun
from app.core.logging import app_logger

class RegressionRunner:
    """
    Compares current benchmark run metrics against historical baselines to flag regressions.
    """
    @classmethod
    async def compare_to_baseline(cls, db: AsyncSession, current_run: EvaluationRun, baseline_run_id: int | None = None) -> dict:
        """
        Compares the new evaluation run to a baseline run.
        """
        if baseline_run_id:
            stmt = select(EvaluationRun).where(EvaluationRun.id == baseline_run_id)
            res = await db.execute(stmt)
            baseline = res.scalars().first()
        else:
            stmt = select(EvaluationRun).where(
                EvaluationRun.run_type == "benchmark",
                EvaluationRun.id != current_run.id
            ).order_by(desc(EvaluationRun.id))
            res = await db.execute(stmt)
            baseline = res.scalars().first()

        if not baseline:
            return {
                "has_regression": False,
                "regressions": [],
                "baseline_run_id": None,
                "message": "No historical baseline runs found for comparison."
            }

        regressions = []
        threshold = 0.05

        overall_diff = baseline.overall_score - current_run.overall_score
        if overall_diff > threshold:
            regressions.append({
                "category": "overall",
                "baseline_score": baseline.overall_score,
                "current_score": current_run.overall_score,
                "drop": round(overall_diff, 2)
            })

        for cat, base_val in baseline.category_scores.items():
            curr_val = current_run.category_scores.get(cat, 0.0)
            diff = base_val - curr_val
            if diff > threshold:
                regressions.append({
                    "category": cat,
                    "baseline_score": base_val,
                    "current_score": curr_val,
                    "drop": round(diff, 2)
                })

        has_regression = len(regressions) > 0
        if has_regression:
            app_logger.warning(
                "ai_quality_regression_detected",
                run_id=current_run.id,
                baseline_id=baseline.id,
                regressions=regressions
            )
            current_run.baseline_run_id = baseline.id
            await db.commit()

        return {
            "has_regression": has_regression,
            "regressions": regressions,
            "baseline_run_id": baseline.id,
            "message": f"Regression evaluation complete against baseline run #{baseline.id}."
        }
