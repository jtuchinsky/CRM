"""Recommendation value objects - pure domain, zero framework dependencies."""

from dataclasses import dataclass
from enum import Enum


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class TaskRecommendation:
    """Value object representing an AI-suggested task."""

    title: str
    description: str
    priority: str  # "low", "medium", "high"
    due_date: str | None = None

    def __post_init__(self):
        """Validate task recommendation fields."""
        if not self.title:
            raise ValueError("Task title cannot be empty")
        if not self.description:
            raise ValueError("Task description cannot be empty")
        if self.priority not in ["low", "medium", "high"]:
            raise ValueError(f"Priority must be low, medium, or high, got {self.priority}")


@dataclass(frozen=True)
class DealRecommendation:
    """Value object representing an AI-suggested deal/pipeline entry."""

    contact_email: str
    deal_stage: str
    value: float
    notes: str

    def __post_init__(self):
        """Validate deal recommendation fields."""
        if not self.contact_email or "@" not in self.contact_email:
            raise ValueError(f"Invalid contact email: {self.contact_email}")
        if not self.deal_stage:
            raise ValueError("Deal stage cannot be empty")
        if self.value < 0:
            raise ValueError(f"Deal value must be non-negative, got {self.value}")
        if not self.notes:
            raise ValueError("Deal notes cannot be empty")
