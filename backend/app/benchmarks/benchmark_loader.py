import os
import json
import yaml
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.evaluation import BenchmarkCase
from app.core.logging import app_logger

class BenchmarkLoader:
    """
    Utility that parses benchmark cases from JSON/YAML and inserts them into the DB.
    """
    @staticmethod
    def load_from_file(filepath: str) -> list[dict]:
        """
        Reads datasets dynamically based on file extension.
        """
        if not os.path.exists(filepath):
            app_logger.warning("benchmark_file_not_found", path=filepath)
            return []

        _, ext = os.path.splitext(filepath.lower())
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                if ext in (".yaml", ".yml"):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "benchmarks" in data:
                    return data["benchmarks"]
                return []
        except Exception as exc:
            app_logger.error("failed_to_load_benchmarks", path=filepath, error=str(exc))
            return []

    @classmethod
    async def seed_benchmarks(cls, db: AsyncSession, filepath: str) -> int:
        """
        Seeds benchmarks from JSON or YAML if they are not already in DB.
        """
        cases_data = cls.load_from_file(filepath)
        if not cases_data:
            return 0

        added_count = 0
        for case in cases_data:
            stmt = select(BenchmarkCase).where(BenchmarkCase.question == case["question"])
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if not existing:
                new_case = BenchmarkCase(
                    question=case["question"],
                    expected_answer=case["expected_answer"],
                    expected_sources=case.get("expected_sources"),
                    expected_documents=case.get("expected_documents"),
                    expected_keywords=case.get("expected_keywords"),
                    category=case.get("category", "General"),
                    difficulty=case.get("difficulty", "Medium"),
                    ground_truth=case.get("ground_truth", "")
                )
                db.add(new_case)
                added_count += 1

        if added_count > 0:
            await db.commit()
            app_logger.info("seeded_benchmark_cases", count=added_count)

        return added_count
