"""Normalized email domain entity - pure domain, zero framework dependencies."""

from dataclasses import dataclass
from datetime import datetime

from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders


@dataclass
class NormalizedEmail:
    """Domain entity representing a normalized email message."""

    from_address: EmailAddress
    to_addresses: list[EmailAddress]
    headers: EmailHeaders
    body: EmailBody
    cc_addresses: list[EmailAddress] | None = None
    bcc_addresses: list[EmailAddress] | None = None
    received_at: datetime | None = None

    def is_reply(self) -> bool:
        """Check if this email is a reply to another message."""
        # Check for "Re:" prefix in subject
        if self.headers.subject.lower().startswith("re:"):
            return True

        # Check for in_reply_to header
        if self.headers.in_reply_to:
            return True

        # Check for references header
        if self.headers.references and len(self.headers.references) > 0:
            return True

        return False

    def get_thread_id(self) -> str | None:
        """Get the thread ID for email threading."""
        # Prefer explicit thread_id from headers
        if self.headers.thread_id:
            return self.headers.thread_id

        # Fall back to first reference (oldest message in thread)
        if self.headers.references and len(self.headers.references) > 0:
            return self.headers.references[0]

        # Fall back to in_reply_to
        if self.headers.in_reply_to:
            return self.headers.in_reply_to

        # Use own message_id for new thread
        return self.headers.message_id

    def extract_sender_name(self) -> str:
        """Extract sender name, falling back to email address."""
        if self.from_address.name:
            return self.from_address.name
        # Extract name from email local part
        local_part = self.from_address.email.split("@")[0]
        # Replace common separators with spaces
        return local_part.replace(".", " ").replace("_", " ").title()

    def get_primary_recipient(self) -> EmailAddress | None:
        """Get the first 'to' recipient."""
        if self.to_addresses and len(self.to_addresses) > 0:
            return self.to_addresses[0]
        return None

    def has_attachments(self) -> bool:
        """Check if email likely has attachments (placeholder - needs implementation)."""
        # TODO: Add attachment handling in future phase
        return False
