"""Email normalizer port - interface for email normalization service."""

from abc import ABC, abstractmethod

from app.core.domain.models.normalized_email import NormalizedEmail


class EmailNormalizerPort(ABC):
    """Port for normalizing raw email payloads into domain entities."""

    @abstractmethod
    async def normalize(self, raw_email: dict) -> NormalizedEmail:
        """
        Normalize raw email payload to NormalizedEmail domain entity.

        Args:
            raw_email: Raw email payload from webhook or email provider

        Returns:
            NormalizedEmail domain entity with cleaned content

        Raises:
            ValueError: If email payload is invalid or missing required fields
        """
        pass
