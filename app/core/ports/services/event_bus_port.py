"""Event bus port - interface for publishing domain events."""

from abc import ABC, abstractmethod

from app.core.domain.events import EmailIntakeProcessed, UserDecisionSubmitted


class EventBusPort(ABC):
    """Port for publishing domain events to event bus / message queue."""

    @abstractmethod
    async def publish(self, event: EmailIntakeProcessed | UserDecisionSubmitted) -> None:
        """
        Publish domain event to event bus.

        Args:
            event: Domain event to publish

        Raises:
            RuntimeError: If event bus is unavailable
        """
        pass
