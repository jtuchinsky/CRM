"""EmailIntake ORM model for database persistence."""

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.outbound.db.sqlalchemy.base import IDMixin, TimestampMixin
from app.adapters.outbound.db.sqlalchemy.session import Base


class EmailIntake(Base, IDMixin, TimestampMixin):
    """
    EmailIntake ORM model - stores AI-processed email intake records.

    Uses JSON columns for flexibility to avoid complex joins.
    Quick access fields are denormalized for filtering/searching.
    """

    __tablename__ = "email_intakes"

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # "pending_review", "auto_approved", "user_approved", "rejected"

    # JSON storage for complex nested data
    raw_email_json: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_email_json: Mapped[str] = mapped_column(Text, nullable=False)
    ai_result_json: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=False)
    decision_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalized fields for quick access and filtering
    sender_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Add composite index for common queries
    __table_args__ = (
        Index("idx_email_status_confidence", "status", "confidence_score"),
        Index("idx_email_sender_created", "sender_email", "created_at"),
    )
