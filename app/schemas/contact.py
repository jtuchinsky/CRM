from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactBase(BaseModel):
    """Base schema with shared fields."""

    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    company: str | None = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""

    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact (all fields optional)."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None


class ContactResponse(ContactBase):
    """Schema for contact response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
