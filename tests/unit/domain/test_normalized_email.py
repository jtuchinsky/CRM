"""Unit tests for NormalizedEmail domain entity."""

import pytest
from datetime import datetime

from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.domain.models.normalized_email import NormalizedEmail


class TestEmailAddress:
    """Test EmailAddress value object."""

    def test_create_email_address_with_name(self):
        """Test creating email address with display name."""
        addr = EmailAddress(email="john@example.com", name="John Doe")
        assert addr.email == "john@example.com"
        assert addr.name == "John Doe"
        assert str(addr) == "John Doe <john@example.com>"

    def test_create_email_address_without_name(self):
        """Test creating email address without display name."""
        addr = EmailAddress(email="jane@example.com")
        assert addr.email == "jane@example.com"
        assert addr.name is None
        assert str(addr) == "jane@example.com"

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress(email="not-an-email")


class TestEmailHeaders:
    """Test EmailHeaders value object."""

    def test_create_basic_headers(self):
        """Test creating basic email headers."""
        headers = EmailHeaders(
            subject="Test Subject",
            date=datetime(2025, 12, 15, 10, 0, 0),
            message_id="<msg123@example.com>"
        )
        assert headers.subject == "Test Subject"
        assert headers.message_id == "<msg123@example.com>"

    def test_empty_subject_raises_error(self):
        """Test that empty subject raises ValueError."""
        with pytest.raises(ValueError, match="subject cannot be empty"):
            EmailHeaders(subject="", date=datetime.now())


class TestEmailBody:
    """Test EmailBody value object."""

    def test_create_body_with_text(self):
        """Test creating email body with text."""
        body = EmailBody(raw_text="Hello world", normalized_text="Hello world")
        assert body.has_content()

    def test_create_body_with_html(self):
        """Test creating email body with HTML."""
        body = EmailBody(raw_html="<p>Hello</p>", normalized_text="Hello")
        assert body.has_content()

    def test_empty_body_raises_error(self):
        """Test that completely empty body raises ValueError."""
        with pytest.raises(ValueError, match="At least one body format"):
            EmailBody()


class TestNormalizedEmail:
    """Test NormalizedEmail domain entity."""

    def create_sample_email(
        self,
        subject: str = "Test Subject",
        in_reply_to: str | None = None
    ) -> NormalizedEmail:
        """Helper to create a sample normalized email."""
        return NormalizedEmail(
            from_address=EmailAddress(email="sender@example.com", name="Sender"),
            to_addresses=[EmailAddress(email="recipient@example.com", name="Recipient")],
            headers=EmailHeaders(
                subject=subject,
                date=datetime(2025, 12, 15, 10, 0, 0),
                message_id="<msg1@example.com>",
                in_reply_to=in_reply_to,
            ),
            body=EmailBody(normalized_text="Email content"),
        )

    def test_is_reply_with_re_prefix(self):
        """Test is_reply() detects 'Re:' prefix."""
        email = self.create_sample_email(subject="Re: Original Subject")
        assert email.is_reply() is True

    def test_is_reply_with_in_reply_to_header(self):
        """Test is_reply() detects in-reply-to header."""
        email = self.create_sample_email(
            subject="New Subject",
            in_reply_to="<original@example.com>"
        )
        assert email.is_reply() is True

    def test_is_reply_with_references(self):
        """Test is_reply() detects references header."""
        email = self.create_sample_email()
        email.headers = EmailHeaders(
            subject="Test",
            date=datetime.now(),
            message_id="<msg1@example.com>",
            references=["<original@example.com>"]
        )
        assert email.is_reply() is True

    def test_is_not_reply(self):
        """Test is_reply() returns False for new email."""
        email = self.create_sample_email(subject="New Email")
        assert email.is_reply() is False

    def test_extract_sender_name_with_name(self):
        """Test extract_sender_name() with display name."""
        email = self.create_sample_email()
        assert email.extract_sender_name() == "Sender"

    def test_extract_sender_name_without_name(self):
        """Test extract_sender_name() falls back to email local part."""
        email = self.create_sample_email()
        email.from_address = EmailAddress(email="john.doe@example.com")
        assert email.extract_sender_name() == "John Doe"

    def test_get_thread_id_uses_thread_id(self):
        """Test get_thread_id() prefers explicit thread_id."""
        email = self.create_sample_email()
        email.headers = EmailHeaders(
            subject="Test",
            date=datetime.now(),
            message_id="<msg1@example.com>",
            thread_id="<thread123@example.com>"
        )
        assert email.get_thread_id() == "<thread123@example.com>"

    def test_get_thread_id_falls_back_to_references(self):
        """Test get_thread_id() falls back to first reference."""
        email = self.create_sample_email()
        email.headers = EmailHeaders(
            subject="Test",
            date=datetime.now(),
            message_id="<msg1@example.com>",
            references=["<original@example.com>", "<reply@example.com>"]
        )
        assert email.get_thread_id() == "<original@example.com>"

    def test_get_primary_recipient(self):
        """Test get_primary_recipient() returns first to address."""
        email = self.create_sample_email()
        recipient = email.get_primary_recipient()
        assert recipient is not None
        assert recipient.email == "recipient@example.com"
