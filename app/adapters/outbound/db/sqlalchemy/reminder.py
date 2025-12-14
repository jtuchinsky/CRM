from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.outbound.db.sqlalchemy.base import IDMixin, TimestampMixin
from app.adapters.outbound.db.sqlalchemy.session import Base


class ReminderType(str, Enum):
    """Type of reminder delivery."""

    EMAIL = "email"
    SMS = "sms"


class ReminderStatus(str, Enum):
    """Status of reminder sending."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Reminder(Base, IDMixin, TimestampMixin):
    """Reminder for appointments - tracks scheduled and sent reminders."""

    __tablename__ = "reminders"

    # Foreign key
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Reminder details
    reminder_type: Mapped[str] = mapped_column(String(10), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(10), default=ReminderStatus.PENDING.value, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="reminders")
