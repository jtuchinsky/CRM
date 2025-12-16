"""Email intake result domain entities - pure domain, zero framework dependencies."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, ExtractedEntity, Intent, Summary
from app.core.domain.value_objects.recommendation import (
    DealRecommendation,
    RecommendationStatus,
    TaskRecommendation,
)


@dataclass
class AIIntakeResult:
    """Domain entity representing AI analysis results."""

    summary: Summary
    intent: Intent
    entities: list[ExtractedEntity]
    confidence: Confidence

    def get_high_confidence_entities(self, threshold: float = 0.7) -> list[ExtractedEntity]:
        """Get entities with confidence above threshold."""
        return [entity for entity in self.entities if entity.confidence >= threshold]

    def has_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if overall confidence is high."""
        return self.confidence.is_high(threshold)


@dataclass
class Recommendations:
    """Domain entity representing AI-generated recommendations."""

    tasks: list[TaskRecommendation] = field(default_factory=list)
    deals: list[DealRecommendation] = field(default_factory=list)

    def has_recommendations(self) -> bool:
        """Check if there are any recommendations."""
        return len(self.tasks) > 0 or len(self.deals) > 0

    def count_total(self) -> int:
        """Get total number of recommendations."""
        return len(self.tasks) + len(self.deals)


@dataclass
class IntakeDecision:
    """Value object representing user decision on recommendations."""

    approved_task_indices: list[int] = field(default_factory=list)
    approved_deal_indices: list[int] = field(default_factory=list)
    rejected_task_indices: list[int] = field(default_factory=list)
    rejected_deal_indices: list[int] = field(default_factory=list)
    decided_at: datetime | None = None
    decided_by: str | None = None  # User ID or email

    def has_approvals(self) -> bool:
        """Check if any items were approved."""
        return len(self.approved_task_indices) > 0 or len(self.approved_deal_indices) > 0


@dataclass
class IntakeRecord:
    """Aggregate root for email intake process."""

    normalized_email: NormalizedEmail
    ai_result: AIIntakeResult
    recommendations: Recommendations
    status: str  # "pending_review", "auto_approved", "user_approved", "rejected"
    id: int | None = None
    decision: IntakeDecision | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def should_auto_approve(self, threshold: float = 0.85) -> bool:
        """
        Determine if this intake should be auto-approved based on confidence.

        Uses ConfidencePolicy threshold (will be imported from policies in Phase 2).
        """
        return self.ai_result.confidence.overall_score >= threshold

    def requires_human_review(self, threshold: float = 0.85) -> bool:
        """
        Determine if this intake requires human review.

        Inverse of should_auto_approve.
        """
        return not self.should_auto_approve(threshold)

    def is_decided(self) -> bool:
        """Check if user has made a decision."""
        return self.decision is not None and self.decision.has_approvals()

    def get_sender_email(self) -> str:
        """Get sender email address for quick access."""
        return self.normalized_email.from_address.email

    def get_subject(self) -> str:
        """Get email subject for quick access."""
        return self.normalized_email.headers.subject

    def get_confidence_score(self) -> float:
        """Get AI confidence score for quick access."""
        return self.ai_result.confidence.overall_score
