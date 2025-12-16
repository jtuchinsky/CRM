"""Email normalizer adapter - cleans and normalizes email content."""

import re
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.ports.services.email_normalizer_port import EmailNormalizerPort


class EmailNormalizer(EmailNormalizerPort):
    """
    Normalizes raw email payloads into clean NormalizedEmail domain entities.

    Handles:
    - HTML stripping and cleaning
    - Quoted reply removal
    - Email signature removal
    - Metadata extraction
    """

    async def normalize(self, raw_email: dict) -> NormalizedEmail:
        """
        Normalize raw email payload to NormalizedEmail domain entity.

        Args:
            raw_email: Raw email payload with keys like:
                - from: sender email (str) or dict with email/name
                - to: recipient(s)
                - subject: email subject
                - body_html: HTML body (optional)
                - body_text: plain text body (optional)
                - date: date string or datetime
                - message_id: unique message ID (optional)
                - in_reply_to: replied message ID (optional)
                - references: list of message IDs (optional)

        Returns:
            NormalizedEmail domain entity

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract from address
        from_address = self._parse_email_address(raw_email.get("from"))
        if not from_address:
            raise ValueError("Missing or invalid 'from' address")

        # Extract to addresses
        to_addresses = self._parse_email_addresses(raw_email.get("to", []))
        if not to_addresses:
            raise ValueError("Missing or invalid 'to' addresses")

        # Extract CC/BCC (optional)
        cc_addresses = self._parse_email_addresses(raw_email.get("cc", []))
        bcc_addresses = self._parse_email_addresses(raw_email.get("bcc", []))

        # Extract and parse date
        date = self._parse_date(raw_email.get("date"))

        # Build email headers
        headers = EmailHeaders(
            subject=raw_email.get("subject", "(No Subject)"),
            date=date,
            message_id=raw_email.get("message_id"),
            thread_id=raw_email.get("thread_id"),
            in_reply_to=raw_email.get("in_reply_to"),
            references=raw_email.get("references", []) if raw_email.get("references") else None,
        )

        # Extract and clean body
        raw_html = raw_email.get("body_html")
        raw_text = raw_email.get("body_text")

        normalized_text = await self._clean_body(raw_html, raw_text)

        body = EmailBody(
            raw_html=raw_html,
            raw_text=raw_text,
            normalized_text=normalized_text,
        )

        return NormalizedEmail(
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses if cc_addresses else None,
            bcc_addresses=bcc_addresses if bcc_addresses else None,
            headers=headers,
            body=body,
            received_at=datetime.now(),
        )

    def _parse_email_address(self, addr_data: str | dict | None) -> EmailAddress | None:
        """Parse email address from string or dict."""
        if not addr_data:
            return None

        if isinstance(addr_data, str):
            # Simple string: "john@example.com" or "John Doe <john@example.com>"
            match = re.match(r"(.+?)\s*<(.+?)>", addr_data)
            if match:
                name, email = match.groups()
                return EmailAddress(email=email.strip(), name=name.strip())
            return EmailAddress(email=addr_data.strip())

        if isinstance(addr_data, dict):
            return EmailAddress(
                email=addr_data.get("email", ""),
                name=addr_data.get("name"),
            )

        return None

    def _parse_email_addresses(self, addr_list: list | str | None) -> list[EmailAddress]:
        """Parse multiple email addresses."""
        if not addr_list:
            return []

        if isinstance(addr_list, str):
            # Split by comma or semicolon
            addr_list = re.split(r"[,;]", addr_list)

        addresses = []
        for addr in addr_list:
            parsed = self._parse_email_address(addr)
            if parsed:
                addresses.append(parsed)

        return addresses

    def _parse_date(self, date_str: str | datetime | None) -> datetime:
        """Parse date from string or datetime."""
        if isinstance(date_str, datetime):
            return date_str

        if isinstance(date_str, str):
            try:
                return date_parser.parse(date_str)
            except (ValueError, TypeError):
                pass

        # Fallback to now
        return datetime.now()

    async def _clean_body(self, html: str | None, text: str | None) -> str:
        """
        Clean email body content.

        Priority: HTML > plain text
        Removes: HTML tags, quoted replies, signatures
        """
        if html:
            return self._clean_html(html)

        if text:
            return self._clean_text(text)

        return ""

    def _clean_html(self, html: str) -> str:
        """Clean HTML email body."""
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style tags
        for tag in soup(["script", "style", "head", "title"]):
            tag.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        # Remove quoted replies
        text = self._remove_quoted_replies(text)

        # Remove signatures
        text = self._remove_signatures(text)

        return text.strip()

    def _clean_text(self, text: str) -> str:
        """Clean plain text email body."""
        # Remove quoted replies
        text = self._remove_quoted_replies(text)

        # Remove signatures
        text = self._remove_signatures(text)

        return text.strip()

    def _remove_quoted_replies(self, text: str) -> str:
        """
        Remove quoted reply sections.

        Patterns:
        - Lines starting with >
        - "On [date], [person] wrote:"
        - Gmail/Outlook quote markers
        """
        lines = text.split("\n")
        cleaned = []

        in_quote = False
        for line in lines:
            stripped = line.strip()

            # Check for quote start patterns
            if stripped.startswith(">"):
                in_quote = True
                continue

            if re.match(r"On .+ wrote:", stripped):
                in_quote = True
                continue

            if "-----Original Message-----" in stripped:
                in_quote = True
                continue

            if in_quote and not stripped:
                # Empty line might end quote
                in_quote = False
                continue

            if not in_quote:
                cleaned.append(line)

        return "\n".join(cleaned)

    def _remove_signatures(self, text: str) -> str:
        """
        Remove email signatures.

        Common patterns:
        - Lines starting with --
        - "Sent from my iPhone"
        - "Best regards" followed by name
        """
        # Split by signature markers
        patterns = [
            r"\n--\s*\n",  # Standard -- delimiter
            r"\n_{3,}\n",  # Underscores
            r"\nSent from my",  # Mobile signatures
            r"\nGet Outlook for",  # Outlook mobile
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                text = text[: match.start()]

        return text.strip()
