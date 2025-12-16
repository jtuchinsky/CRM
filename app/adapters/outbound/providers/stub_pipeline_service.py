"""Stub pipeline service adapter - logs deal creation."""

import logging

from app.core.ports.services.pipeline_command_port import PipelineCommandPort

logger = logging.getLogger(__name__)


class StubPipelineService(PipelineCommandPort):
    """
    Stub implementation of PipelineCommandPort that logs deal creation.

    In production, this would call a real Pipeline/Deal Service API or create
    deals directly in the database. For MVP, we just log and return a fake ID.
    """

    _deal_counter = 2000  # Start at 2000 for stub IDs

    async def create_deal(
        self,
        contact_email: str,
        stage: str,
        value: float,
        notes: str,
    ) -> dict:
        """
        Log deal creation and return stub deal dict.

        Args:
            contact_email: Contact email for this deal
            stage: Deal stage (e.g., "qualification", "proposal", "negotiation")
            value: Estimated deal value
            notes: Deal notes/description

        Returns:
            Stub deal dict with fake ID

        Raises:
            ValueError: Never raised in stub (always succeeds)
        """
        StubPipelineService._deal_counter += 1
        deal_id = StubPipelineService._deal_counter

        logger.warning(
            f"⚠️  STUB: PipelineService.create_deal | "
            f"ID: {deal_id} | "
            f"Contact: {contact_email} | "
            f"Stage: {stage} | "
            f"Value: ${value:.2f}"
        )

        return {
            "id": deal_id,
            "contact_email": contact_email,
            "stage": stage,
            "value": value,
            "notes": notes,
            "status": "stub_created",
            "note": "This is a stub - deal not actually created",
        }

        # TODO Phase 7: Replace with real Pipeline Service implementation
