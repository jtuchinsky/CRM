"""Stub event bus adapter - logs events to console."""

import logging

from app.core.domain.events import EmailIntakeProcessed, UserDecisionSubmitted
from app.core.ports.services.event_bus_port import EventBusPort

logger = logging.getLogger(__name__)


class StubEventBus(EventBusPort):
    """
    Stub implementation of EventBusPort that logs events to console.

    In production, this would publish to a real message queue (RabbitMQ, Redis, etc.).
    For MVP, we just log the events.
    """

    async def publish(self, event: EmailIntakeProcessed | UserDecisionSubmitted) -> None:
        """
        Log domain event to console.

        Args:
            event: Domain event to publish

        Raises:
            RuntimeError: Never raised in stub (always succeeds)
        """
        event_type = type(event).__name__

        if isinstance(event, EmailIntakeProcessed):
            logger.info(
                f"📧 EVENT: {event_type} | "
                f"Intake ID: {event.intake_id} | "
                f"Status: {event.status} | "
                f"Confidence: {event.confidence_score:.2f} | "
                f"From: {event.sender_email} | "
                f"Subject: {event.subject}"
            )
        elif isinstance(event, UserDecisionSubmitted):
            logger.info(
                f"✅ EVENT: {event_type} | "
                f"Intake ID: {event.intake_id} | "
                f"Tasks approved: {event.approved_task_count} | "
                f"Deals approved: {event.approved_deal_count} | "
                f"Decided by: {event.decided_by or 'unknown'}"
            )
        else:
            logger.info(f"📨 EVENT: {event_type} | {event}")

        # TODO Phase 6: Replace with real event bus (RabbitMQ, Redis Pub/Sub, etc.)
