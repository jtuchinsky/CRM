from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.adapters.outbound.db.sqlalchemy.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    """Base schema with shared fields."""

    contact_id: int
    staff_id: int
    start_time: datetime
    duration_minutes: int
    title: str
    description: str | None = None
    location: str | None = None


class AppointmentCreate(AppointmentBase):
    """Schema for creating appointment."""

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0 or v > 480:  # Max 8 hours
            raise ValueError("Duration must be between 1 and 480 minutes")
        return v


class AppointmentUpdate(BaseModel):
    """Schema for updating appointment (all fields optional)."""

    start_time: datetime | None = None
    duration_minutes: int | None = None
    title: str | None = None
    description: str | None = None
    location: str | None = None
    status: AppointmentStatus | None = None


class AppointmentResponse(AppointmentBase):
    """Schema for appointment response."""

    id: int
    end_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeSlotResponse(BaseModel):
    """Schema for available time slot."""

    start_time: datetime
    end_time: datetime
