"""AI intake port - interface for AI-powered email analysis service."""

from abc import ABC, abstractmethod

from app.core.domain.models.intake_result import AIIntakeResult
from app.core.domain.models.normalized_email import NormalizedEmail


class AIIntakePort(ABC):
    """Port for AI-powered email analysis and recommendation generation."""

    @abstractmethod
    async def analyze(
        self,
        email: NormalizedEmail,
        context: dict,
    ) -> AIIntakeResult:
        """
        Use LLM to analyze email and generate recommendations.

        Args:
            email: Normalized email domain entity
            context: CRM context (contact info, recent interactions, etc.)

        Returns:
            AIIntakeResult with summary, intent, entities, and recommendations

        Raises:
            ValueError: If email analysis fails
            RuntimeError: If LLM service is unavailable
        """
        pass
