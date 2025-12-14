from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StaffBase(BaseModel):
    """Base schema with shared fields."""

    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    role: str
    is_active: bool = True


class StaffCreate(StaffBase):
    """Schema for creating staff."""

    pass


class StaffUpdate(BaseModel):
    """Schema for updating staff (all fields optional)."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    is_active: bool | None = None


class StaffResponse(StaffBase):
    """Schema for staff response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
