from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.staff_availability import AvailabilityType


class StaffAvailabilityBase(BaseModel):
    """Base schema with shared fields."""

    availability_type: AvailabilityType
    day_of_week: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_recurring: bool = True
    specific_date: datetime | None = None
    specific_start: datetime | None = None
    specific_end: datetime | None = None
    is_available: bool = True
    notes: str | None = None


class StaffAvailabilityCreate(StaffAvailabilityBase):
    """Schema for creating availability."""

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v: int | None) -> int | None:
        if v is not None and (v < 0 or v > 6):
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        return v


class StaffAvailabilityUpdate(BaseModel):
    """Schema for updating availability (all fields optional)."""

    availability_type: AvailabilityType | None = None
    day_of_week: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_recurring: bool | None = None
    specific_date: datetime | None = None
    specific_start: datetime | None = None
    specific_end: datetime | None = None
    is_available: bool | None = None
    notes: str | None = None


class StaffAvailabilityResponse(StaffAvailabilityBase):
    """Schema for availability response."""

    id: int
    staff_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
