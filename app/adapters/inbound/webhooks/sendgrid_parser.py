"""SendGrid webhook parser adapter."""

import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

from app.core.ports.services.webhook_parser_port import WebhookParserPort


class SendGridWebhookParser(WebhookParserPort):
    """
    Parse SendGrid Inbound Parse webhooks.

    SendGrid documentation:
    https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook
    """

    def parse(self, payload: dict, headers: dict) -> dict:
        """
        Parse SendGrid webhook payload into generic email format.

        SendGrid sends webhooks with these key fields:
        - from: sender email
        - to: recipient email
        - subject: email subject
        - text: plain text body
        - html: HTML body
        - headers: JSON string of email headers
        - attachments: number of attachments

        Args:
            payload: SendGrid webhook payload
            headers: HTTP headers

        Returns:
            Generic email dict

        Raises:
            ValueError: If required fields are missing
        """
        # Extract required fields
        from_email = payload.get("from")
        to_email = payload.get("to")
        subject = payload.get("subject")

        if not from_email or not to_email:
            raise ValueError("Missing required fields: 'from' or 'to'")

        # Parse email headers if present
        email_headers = {}
        if "headers" in payload and isinstance(payload["headers"], str):
            try:
                email_headers = json.loads(payload["headers"])
            except json.JSONDecodeError:
                # If headers are not JSON, skip them
                pass

        # Extract message ID from headers or generate one
        message_id = email_headers.get("Message-ID") or email_headers.get("Message-Id")
        if not message_id:
            # Generate a pseudo message ID from SendGrid envelope
            envelope = payload.get("envelope", "{}")
            try:
                envelope_dict = json.loads(envelope) if isinstance(envelope, str) else envelope
                message_id = f"<{envelope_dict.get('from', from_email)}@sendgrid>"
            except (json.JSONDecodeError, AttributeError):
                message_id = f"<{from_email}@sendgrid>"

        # Parse date
        date_str = email_headers.get("Date")
        if not date_str:
            date_str = datetime.now().isoformat()

        # Build generic email format
        generic_email = {
            "from": from_email,
            "to": self._parse_recipients(to_email),
            "subject": subject or "(No Subject)",
            "text": payload.get("text"),
            "html": payload.get("html"),
            "date": date_str,
            "message_id": message_id,
            "in_reply_to": email_headers.get("In-Reply-To"),
            "references": self._parse_references(email_headers.get("References")),
        }

        # Add CC if present
        cc = payload.get("cc")
        if cc:
            generic_email["cc"] = self._parse_recipients(cc)

        return generic_email

    def validate(self, payload: dict, headers: dict, secret: str) -> bool:
        """
        Validate SendGrid webhook signature.

        SendGrid uses HMAC SHA256 signatures in the
        'X-Twilio-Email-Event-Webhook-Signature' header (for Event Webhook)
        or basic auth for Inbound Parse.

        For Inbound Parse, there's no built-in signature validation,
        so we rely on HTTPS and optional basic auth.

        Args:
            payload: Webhook payload
            headers: HTTP headers
            secret: Shared secret (not used for Inbound Parse)

        Returns:
            True (Inbound Parse doesn't have signature validation)
        """
        # SendGrid Inbound Parse doesn't provide signature validation
        # Validation relies on:
        # 1. HTTPS (enforced at infrastructure level)
        # 2. Webhook URL secrecy (use long random path)
        # 3. Optional: Custom header validation

        # Check for custom validation header if configured
        validation_header = headers.get("X-SendGrid-Validation")
        if secret and validation_header:
            # If secret is configured, validate custom header
            return hmac.compare_digest(validation_header, secret)

        # Otherwise, accept all webhooks (rely on URL secrecy)
        return True

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
