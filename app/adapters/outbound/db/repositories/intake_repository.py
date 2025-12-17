"""Intake repository adapter - persists IntakeRecord domain entities."""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.outbound.db.sqlalchemy.email_intake import EmailIntake
from app.core.domain.models.intake_result import (
    AIIntakeResult,
    IntakeDecision,
    IntakeRecord,
    Recommendations,
)
from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, ExtractedEntity, Intent, Summary
from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.domain.value_objects.recommendation import (
    DealRecommendation,
    TaskRecommendation,
)
from app.core.ports.repositories.intake_repository_port import IntakeRepositoryPort


class IntakeRepository(IntakeRepositoryPort):
    """
    Intake repository implementation using SQLAlchemy.

    Responsibilities:
    - Convert IntakeRecord (domain) ↔ EmailIntake (ORM)
    - JSON serialization/deserialization of complex nested objects
    - CRUD operations on email_intakes table
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def save(self, intake: IntakeRecord) -> IntakeRecord:
        """
        Persist intake record to database.

        Args:
            intake: Domain entity to save

        Returns:
            IntakeRecord with assigned ID and timestamps
        """
        # Convert domain entity to ORM model
        orm_model = self._to_orm(intake)

        self.db.add(orm_model)
        await self.db.flush()
        await self.db.refresh(orm_model)

        # Convert back to domain entity with new ID
        return self._to_domain(orm_model)

    async def get_by_id(self, intake_id: int) -> IntakeRecord | None:
        """
        Retrieve intake record by ID.

        Args:
            intake_id: Primary key

        Returns:
            IntakeRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(EmailIntake).where(EmailIntake.id == intake_id)
        )
        orm_model = result.scalar_one_or_none()

        if not orm_model:
            return None

        return self._to_domain(orm_model)

    async def list_pending_reviews(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[IntakeRecord]:
        """
        List intake records pending human review.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of IntakeRecord entities with status='pending_review'
        """
        result = await self.db.execute(
            select(EmailIntake)
            .where(EmailIntake.status == "pending_review")
            .order_by(EmailIntake.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        orm_models = result.scalars().all()

        return [self._to_domain(model) for model in orm_models]

    async def update_decision(
        self,
        intake_id: int,
        decision: IntakeDecision,
    ) -> IntakeRecord:
        """
        Update intake record with user decision.

        Args:
            intake_id: Primary key
            decision: User's decision on recommendations

        Returns:
            Updated IntakeRecord

        Raises:
            ValueError: If intake not found
        """
        result = await self.db.execute(
            select(EmailIntake).where(EmailIntake.id == intake_id)
        )
        orm_model = result.scalar_one_or_none()

        if not orm_model:
            raise ValueError(f"Intake record not found: {intake_id}")

        # Determine status based on decision
        if decision.has_approvals():
            orm_model.status = "user_approved"
        else:
            orm_model.status = "rejected"

        # Serialize decision with datetime handling
        decision_dict = self._serialize_datetime(asdict(decision))
        orm_model.decision_json = json.dumps(decision_dict)
        orm_model.updated_at = datetime.now()

        await self.db.flush()
        await self.db.refresh(orm_model)

        return self._to_domain(orm_model)

    # --- Conversion Methods ---

    def _serialize_datetime(self, obj: Any) -> Any:
        """
        Recursively convert datetime objects to ISO format strings for JSON serialization.

        Args:
            obj: Object that may contain datetime instances

        Returns:
            Object with datetime instances converted to ISO strings
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        return obj

    def _to_orm(self, intake: IntakeRecord) -> EmailIntake:
        """
        Convert domain entity to ORM model.

        Args:
            intake: IntakeRecord domain entity

        Returns:
            EmailIntake ORM model
        """
        # Serialize complex objects to JSON
        normalized_email_dict = {
            "from_address": asdict(intake.normalized_email.from_address),
            "to_addresses": [asdict(addr) for addr in intake.normalized_email.to_addresses],
            "cc_addresses": [asdict(addr) for addr in intake.normalized_email.cc_addresses] if intake.normalized_email.cc_addresses else [],
            "headers": asdict(intake.normalized_email.headers),
            "body": asdict(intake.normalized_email.body),
        }

        ai_result_dict = {
            "summary": asdict(intake.ai_result.summary),
            "intent": intake.ai_result.intent.value,
            "entities": [asdict(entity) for entity in intake.ai_result.entities],
            "confidence": asdict(intake.ai_result.confidence),
        }

        recommendations_dict = {
            "tasks": [asdict(task) for task in intake.recommendations.tasks],
            "deals": [asdict(deal) for deal in intake.recommendations.deals],
        }

        decision_json = None
        if intake.decision:
            decision_dict = self._serialize_datetime(asdict(intake.decision))
            decision_json = json.dumps(decision_dict)

        return EmailIntake(
            id=intake.id,
            status=intake.status,
            raw_email_json=json.dumps(getattr(intake, 'raw_email', {})),
            normalized_email_json=json.dumps(self._serialize_datetime(normalized_email_dict)),
            ai_result_json=json.dumps(self._serialize_datetime(ai_result_dict)),
            recommendations_json=json.dumps(self._serialize_datetime(recommendations_dict)),
            decision_json=decision_json,
            sender_email=intake.normalized_email.from_address.email,
            subject=intake.normalized_email.headers.subject,
            confidence_score=intake.ai_result.confidence.overall_score,
            created_at=intake.created_at,
            updated_at=intake.updated_at,
        )

    def _to_domain(self, orm_model: EmailIntake) -> IntakeRecord:
        """
        Convert ORM model to domain entity.

        Args:
            orm_model: EmailIntake ORM model

        Returns:
            IntakeRecord domain entity
        """
        # Deserialize JSON to domain objects
        # Note: raw_email is stored but not part of domain entity
        normalized_dict = json.loads(orm_model.normalized_email_json)
        normalized_email = NormalizedEmail(
            from_address=EmailAddress(**normalized_dict["from_address"]),
            to_addresses=[EmailAddress(**addr) for addr in normalized_dict["to_addresses"]],
            cc_addresses=[EmailAddress(**addr) for addr in normalized_dict.get("cc_addresses", [])],
            headers=EmailHeaders(**normalized_dict["headers"]),
            body=EmailBody(**normalized_dict["body"]),
        )

        ai_result_dict = json.loads(orm_model.ai_result_json)
        ai_result = AIIntakeResult(
            summary=Summary(**ai_result_dict["summary"]),
            intent=Intent(ai_result_dict["intent"]),
            entities=[ExtractedEntity(**entity) for entity in ai_result_dict["entities"]],
            confidence=Confidence(**ai_result_dict["confidence"]),
        )

        recommendations_dict = json.loads(orm_model.recommendations_json)
        recommendations = Recommendations(
            tasks=[TaskRecommendation(**task) for task in recommendations_dict["tasks"]],
            deals=[DealRecommendation(**deal) for deal in recommendations_dict["deals"]],
        )

        decision = None
        if orm_model.decision_json:
            decision_dict = json.loads(orm_model.decision_json)
            decision = IntakeDecision(
                approved_task_indices=decision_dict.get("approved_task_indices", []),
                approved_deal_indices=decision_dict.get("approved_deal_indices", []),
                rejected_task_indices=decision_dict.get("rejected_task_indices", []),
                rejected_deal_indices=decision_dict.get("rejected_deal_indices", []),
                created_tasks=decision_dict.get("created_tasks", []),
                created_deals=decision_dict.get("created_deals", []),
                notes=decision_dict.get("notes"),
                decided_at=datetime.fromisoformat(decision_dict["decided_at"]) if decision_dict.get("decided_at") else None,
                decided_by=decision_dict.get("decided_by"),
            )

        return IntakeRecord(
            id=orm_model.id,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=recommendations,
            status=orm_model.status,
            decision=decision,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )
