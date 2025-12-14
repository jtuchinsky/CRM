from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.outbound.db.sqlalchemy.base import IDMixin, TimestampMixin
from app.adapters.outbound.db.sqlalchemy.session import Base


class Contact(Base, IDMixin, TimestampMixin):
    """Contact model - example for CRM skeleton."""

    __tablename__ = "contacts"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
