"""Email metadata value objects - pure domain, zero framework dependencies."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EmailAddress:
    """Value object representing an email address with optional display name."""

    email: str
    name: str | None = None

    def __post_init__(self):
        """Validate email format (basic check)."""
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email address: {self.email}")

    def __str__(self) -> str:
        """Return formatted email address."""
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass(frozen=True)
class EmailHeaders:
    """Value object representing email headers and metadata."""

    subject: str
    date: datetime
    message_id: str | None = None
    thread_id: str | None = None
    in_reply_to: str | None = None
    references: list[str] | None = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.subject:
            raise ValueError("Email subject cannot be empty")


@dataclass(frozen=True)
class EmailBody:
    """Value object representing email body content in various formats."""

    raw_html: str | None = None
    raw_text: str | None = None
    normalized_text: str | None = None

    def __post_init__(self):
        """Validate that at least one content format is provided."""
        if not any([self.raw_html, self.raw_text, self.normalized_text]):
            raise ValueError("At least one body format must be provided")

    def has_content(self) -> bool:
        """Check if email has any content."""
        return bool(self.normalized_text or self.raw_text or self.raw_html)
