from datetime import datetime, time
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import IDMixin, TimestampMixin


class AvailabilityType(str, Enum):
    """Type of availability entry."""

    WORKING_HOURS = "working_hours"  # Regular recurring schedule
    TIME_OFF = "time_off"  # Vacation, sick leave, etc.
    OVERRIDE = "override"  # One-time schedule change


class DayOfWeek(int, Enum):
    """Day of week for recurring schedules."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class StaffAvailability(Base, IDMixin, TimestampMixin):
    """Staff availability including working hours, time off, and schedule overrides."""

    __tablename__ = "staff_availability"

    # Foreign key
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False, index=True)

    # Type of availability
    availability_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Recurring schedule (for WORKING_HOURS)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)  # e.g., 09:00
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)  # e.g., 17:00
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Specific date range (for TIME_OFF or OVERRIDE)
    specific_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    specific_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    specific_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship
    staff: Mapped["Staff"] = relationship("Staff", back_populates="availability_slots")
