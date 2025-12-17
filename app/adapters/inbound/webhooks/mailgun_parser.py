"""Mailgun webhook parser adapter."""

import hashlib
import hmac
from datetime import datetime

from app.core.ports.services.webhook_parser_port import WebhookParserPort


class MailgunWebhookParser(WebhookParserPort):
    """
    Parse Mailgun Route webhooks.

    Mailgun documentation:
    https://documentation.mailgun.com/en/latest/user_manual.html#routes
    """

    def parse(self, payload: dict, headers: dict) -> dict:
        """
        Parse Mailgun webhook payload into generic email format.

        Mailgun sends webhooks with these key fields:
        - sender: sender email
        - recipient: recipient email
        - subject: email subject
        - body-plain: plain text body
        - body-html: HTML body
        - stripped-text: text without quoted parts
        - stripped-html: HTML without quoted parts
        - Message-Id: unique message ID
        - In-Reply-To: replied message ID
        - References: thread references

        Args:
            payload: Mailgun webhook payload
            headers: HTTP headers

        Returns:
            Generic email dict

        Raises:
            ValueError: If required fields are missing
        """
        # Extract required fields
        from_email = payload.get("sender") or payload.get("from")
        to_email = payload.get("recipient") or payload.get("To")
        subject = payload.get("subject") or payload.get("Subject")

        if not from_email or not to_email:
            raise ValueError("Missing required fields: 'sender'/'from' or 'recipient'/'To'")

        # Mailgun provides both raw and stripped versions of the body
        # Prefer stripped versions as they remove quoted replies
        text_body = (
            payload.get("stripped-text")
            or payload.get("body-plain")
            or payload.get("body-text")
        )
        html_body = (
            payload.get("stripped-html")
            or payload.get("body-html")
        )

        # Extract message metadata
        message_id = payload.get("Message-Id") or payload.get("message-id")
        in_reply_to = payload.get("In-Reply-To") or payload.get("in-reply-to")
        references = payload.get("References") or payload.get("references")

        # Parse timestamp
        timestamp = payload.get("timestamp")
        if timestamp:
            try:
                # Mailgun provides Unix timestamp
                date_str = datetime.fromtimestamp(int(timestamp)).isoformat()
            except (ValueError, TypeError):
                date_str = datetime.now().isoformat()
        else:
            date_str = datetime.now().isoformat()

        # Build generic email format
        generic_email = {
            "from": from_email,
            "to": self._parse_recipients(to_email),
            "subject": subject or "(No Subject)",
            "text": text_body,
            "html": html_body,
            "date": date_str,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": self._parse_references(references),
        }

        # Add CC if present
        cc = payload.get("Cc")
        if cc:
            generic_email["cc"] = self._parse_recipients(cc)

        return generic_email

    def validate(self, payload: dict, headers: dict, secret: str) -> bool:
        """
        Validate Mailgun webhook signature.

        Mailgun provides signature validation using:
        - timestamp: Unix timestamp
        - token: Random string
        - signature: HMAC SHA256 of (timestamp + token)

        Args:
            payload: Webhook payload containing signature fields
            headers: HTTP headers
            secret: Mailgun API key (used for HMAC)

        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            # If no secret configured, skip validation (not recommended)
            return True

        # Extract signature fields from payload
        timestamp = payload.get("timestamp")
        token = payload.get("token")
        signature = payload.get("signature")

        if not all([timestamp, token, signature]):
            # Missing signature fields - reject
            return False

        # Compute expected signature
        # Mailgun: HMAC-SHA256(timestamp + token, API key)
        message = f"{timestamp}{token}".encode("utf-8")
        expected_signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=message,
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)

    def _parse_recipients(self, recipients: str | list) -> list[str]:
        """Parse recipient field into list of email addresses."""
        if isinstance(recipients, list):
            return recipients

        if isinstance(recipients, str):
            # Split by comma or semicolon
            import re
            addrs = re.split(r"[,;]\s*", recipients)
            return [addr.strip() for addr in addrs if addr.strip()]

        return []

    def _parse_references(self, references: str | None) -> list[str] | None:
        """Parse References header into list of message IDs."""
        if not references:
            return None

        # References are space-separated message IDs
        refs = references.split()
        return [ref.strip() for ref in refs if ref.strip()]
