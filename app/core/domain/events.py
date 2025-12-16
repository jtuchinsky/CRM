"""Domain events - pure domain, zero framework dependencies."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EmailIntakeProcessed:
    """
    Domain event raised when an email has been processed through AI intake.

    This event signals that:
    - Email has been normalized
    - AI analysis is complete
    - Recommendations have been generated
    - Record has been persisted
    """

    intake_id: int
    timestamp: datetime
    confidence_score: float
    sender_email: str
    subject: str
    status: str  # "pending_review" or "auto_approved"

    def is_auto_approved(self) -> bool:
        """Check if this intake was auto-approved."""
        return self.status == "auto_approved"

    def requires_review(self) -> bool:
        """Check if this intake requires human review."""
        return self.status == "pending_review"


@dataclass(frozen=True)
class UserDecisionSubmitted:
    """
    Domain event raised when user submits a decision on intake recommendations.

    This event signals that:
    - User has reviewed AI recommendations
    - User has approved/rejected specific items
    - Approved items should be created (tasks, deals)
    """

    intake_id: int
    timestamp: datetime
    approved_task_count: int
    approved_deal_count: int
    decided_by: str | None = None  # User ID or email

    def has_approvals(self) -> bool:
        """Check if any items were approved."""
        return self.approved_task_count > 0 or self.approved_deal_count > 0
