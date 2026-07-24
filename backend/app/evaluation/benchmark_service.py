from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.evaluation import BenchmarkCase
from typing import Any

class BenchmarkService:
    """
    CRUD service managing benchmark cases in the database.
    """
    @staticmethod
    async def create_case(db: AsyncSession, case_data: Any) -> BenchmarkCase:
        new_case = BenchmarkCase(
            question=case_data.question,
            expected_answer=case_data.expected_answer,
            expected_sources=case_data.expected_sources,
            expected_documents=case_data.expected_documents,
            expected_keywords=case_data.expected_keywords,
            category=case_data.category,
            difficulty=case_data.difficulty,
            ground_truth=case_data.ground_truth
        )
        db.add(new_case)
        await db.commit()
        await db.refresh(new_case)
        return new_case

    @staticmethod
    async def get_case(db: AsyncSession, case_id: int) -> BenchmarkCase | None:
        stmt = select(BenchmarkCase).where(BenchmarkCase.id == case_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def list_cases(db: AsyncSession) -> list[BenchmarkCase]:
        stmt = select(BenchmarkCase).order_by(BenchmarkCase.id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def delete_case(db: AsyncSession, case_id: int) -> bool:
        case = await BenchmarkService.get_case(db, case_id)
        if not case:
            return False
        await db.execute(delete(BenchmarkCase).where(BenchmarkCase.id == case_id))
        await db.commit()
        return True
