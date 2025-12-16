"""Intake repository port - interface for persistence operations."""

from abc import ABC, abstractmethod

from app.core.domain.models.intake_result import IntakeRecord


class IntakeRepositoryPort(ABC):
    """Port for persisting and retrieving intake records."""

    @abstractmethod
    async def save(self, intake: IntakeRecord) -> IntakeRecord:
        """
        Persist intake record to database.

        Args:
            intake: IntakeRecord domain entity (may or may not have ID)

        Returns:
            IntakeRecord with ID and timestamps populated

        Raises:
            ValueError: If intake validation fails
            RuntimeError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, intake_id: int) -> IntakeRecord | None:
        """
        Retrieve intake record by ID.

        Args:
            intake_id: Unique identifier

        Returns:
            IntakeRecord if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_pending_reviews(self, skip: int = 0, limit: int = 50) -> list[IntakeRecord]:
        """
        List intakes pending human review.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of IntakeRecords with status='pending_review'
        """
        pass

    @abstractmethod
    async def update_decision(self, intake_id: int, decision: dict) -> IntakeRecord:
        """
        Update intake record with user decision.

        Args:
            intake_id: Unique identifier
            decision: Decision dict with approved/rejected items

        Returns:
            Updated IntakeRecord

        Raises:
            ValueError: If intake not found
        """
        pass
