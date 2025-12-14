from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.outbound.db.sqlalchemy.base import IDMixin, TimestampMixin
from app.adapters.outbound.db.sqlalchemy.session import Base


class Staff(Base, IDMixin, TimestampMixin):
    """Staff model for scheduling system."""

    __tablename__ = "staff"

    # Basic info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Role and status
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="staff", lazy="selectin"
    )
    availability_slots: Mapped[list["StaffAvailability"]] = relationship(
        "StaffAvailability", back_populates="staff", lazy="selectin"
    )
