from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.compliance_models import ComplianceStatus, RiskLevel
from .models import Base, DBComplianceScore, DBModelRegistration, DBPolicyViolation, DBRiskAssessment

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    async def get(self, id: Any) -> Optional[T]:
        stmt = (
            select(self.model_cls).where(self.model_cls.model_id == str(id))
            if hasattr(self.model_cls, "model_id")
            else select(self.model_cls).get(id)
        )
        # Adjusting strictly for the primary key lookup
        # Actually sqlalchemy's session.get is better
        return await self.session.get(self.model_cls, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        stmt = select(self.model_cls).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        instance = self.model_cls(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: Any, **kwargs) -> Optional[T]:
        instance = await self.get(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: Any) -> bool:
        instance = await self.get(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True


class ModelRepository(BaseRepository[DBModelRegistration]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBModelRegistration)

    async def get_with_relations(self, model_id: str) -> Optional[DBModelRegistration]:
        stmt = (
            select(DBModelRegistration)
            .options(
                selectinload(DBModelRegistration.compliance_score),
                selectinload(DBModelRegistration.assessments),
                selectinload(DBModelRegistration.violations),
            )
            .where(DBModelRegistration.model_id == model_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(
        self,
        skip: int = 0,
        limit: int = 100,
        risk_level: Optional[RiskLevel] = None,
        compliance_status: Optional[ComplianceStatus] = None,
    ) -> List[DBModelRegistration]:
        stmt = select(DBModelRegistration)

        if risk_level:
            stmt = stmt.where(DBModelRegistration.risk_level == risk_level)

        if compliance_status:
            stmt = stmt.where(DBModelRegistration.compliance_status == compliance_status)

        stmt = stmt.offset(skip).limit(limit).order_by(desc(DBModelRegistration.last_updated_at))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AssessmentRepository(BaseRepository[DBRiskAssessment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBRiskAssessment)

    async def get_latest_for_model(self, model_id: str) -> Optional[DBRiskAssessment]:
        stmt = (
            select(DBRiskAssessment)
            .where(DBRiskAssessment.model_id == model_id)
            .order_by(desc(DBRiskAssessment.assessed_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ViolationRepository(BaseRepository[DBPolicyViolation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBPolicyViolation)

    async def get_active_for_model(self, model_id: str) -> List[DBPolicyViolation]:
        stmt = (
            select(DBPolicyViolation)
            .where(DBPolicyViolation.model_id == model_id)
            .where(DBPolicyViolation.status.in_(["open", "acknowledged", "in_remediation"]))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
