from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import IDMixin, TimestampMixin


class AppointmentStatus(str, Enum):
    """Appointment status lifecycle."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(Base, IDMixin, TimestampMixin):
    """Appointment model linking contacts, staff, and time slots."""

    __tablename__ = "appointments"

    # Foreign keys
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False, index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False, index=True)

    # Scheduling details
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status and metadata
    status: Mapped[str] = mapped_column(
        String(20), default=AppointmentStatus.SCHEDULED.value, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", lazy="selectin")
    staff: Mapped["Staff"] = relationship("Staff", back_populates="appointments", lazy="selectin")
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder", back_populates="appointment", cascade="all, delete-orphan", lazy="selectin"
    )
