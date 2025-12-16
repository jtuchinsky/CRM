"""Pipeline command port - interface for deal/pipeline service operations."""

from abc import ABC, abstractmethod


class PipelineCommandPort(ABC):
    """Port for creating deals in pipeline service (stub in Phase 1)."""

    @abstractmethod
    async def create_deal(
        self,
        contact_email: str,
        stage: str,
        value: float,
        notes: str,
    ) -> dict:
        """
        Create a deal in the pipeline service.

        Args:
            contact_email: Contact email for this deal
            stage: Deal stage (e.g., "qualification", "proposal", "negotiation")
            value: Estimated deal value
            notes: Deal notes/description

        Returns:
            Created deal dict with ID
            Example: {"id": 456, "contact_email": "john@example.com", "status": "created"}

        Raises:
            ValueError: If deal creation fails
        """
        pass
