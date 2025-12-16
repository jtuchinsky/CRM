"""AI analysis result value objects - pure domain, zero framework dependencies."""

from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    """Email intent classification."""

    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    REQUEST = "request"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


@dataclass(frozen=True)
class Summary:
    """Value object representing AI-generated email summary."""

    text: str
    key_points: list[str]

    def __post_init__(self):
        """Validate summary content."""
        if not self.text:
            raise ValueError("Summary text cannot be empty")
        if not isinstance(self.key_points, list):
            raise ValueError("Key points must be a list")


@dataclass(frozen=True)
class ExtractedEntity:
    """Value object representing an entity extracted from email content."""

    entity_type: str  # e.g., "PERSON", "DATE", "MONEY", "ORGANIZATION"
    value: str
    confidence: float

    def __post_init__(self):
        """Validate entity fields."""
        if not self.entity_type:
            raise ValueError("Entity type cannot be empty")
        if not self.value:
            raise ValueError("Entity value cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass(frozen=True)
class Confidence:
    """Value object representing AI confidence score with reasoning."""

    overall_score: float
    reasoning: str

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {self.overall_score}")
        if not self.reasoning:
            raise ValueError("Reasoning cannot be empty")

    def is_high(self, threshold: float = 0.7) -> bool:
        """Check if confidence is above a threshold."""
        return self.overall_score >= threshold

    def is_low(self, threshold: float = 0.4) -> bool:
        """Check if confidence is below a threshold."""
        return self.overall_score < threshold
