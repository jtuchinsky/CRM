"""Generic webhook parser for testing and custom integrations."""

from datetime import datetime

from app.core.ports.services.webhook_parser_port import WebhookParserPort


class GenericWebhookParser(WebhookParserPort):
    """
    Parse generic webhook payloads that already follow our standard format.

    This parser is useful for:
    - Testing and development
    - Custom integrations that send pre-formatted payloads
    - Internal email forwarding

    Expected payload format:
    {
        "from": "sender@example.com",
        "to": ["recipient@example.com"],
        "subject": "Email subject",
        "text": "Plain text body",
        "html": "<p>HTML body</p>",
        "date": "2025-01-01T12:00:00Z",
        "message_id": "<unique-id@example.com>",
        "in_reply_to": "<previous-id@example.com>",  # optional
        "references": ["<ref1@example.com>", ...]    # optional
    }
    """

    def parse(self, payload: dict, headers: dict) -> dict:
        """
        Parse generic webhook payload (pass-through with validation).

        Args:
            payload: Generic webhook payload
            headers: HTTP headers

        Returns:
            Validated generic email dict

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        from_email = payload.get("from")
        to_email = payload.get("to")
        subject = payload.get("subject")

        if not from_email:
            raise ValueError("Missing required field: 'from'")

        if not to_email:
            raise ValueError("Missing required field: 'to'")

        # Normalize to list
        if isinstance(to_email, str):
            to_email = [to_email]

        # Ensure date is present
        date_str = payload.get("date")
        if not date_str:
            date_str = datetime.now().isoformat()

        # Build standardized format
        generic_email = {
            "from": from_email,
            "to": to_email,
            "subject": subject or "(No Subject)",
            "text": payload.get("text") or payload.get("body_text"),
            "html": payload.get("html") or payload.get("body_html"),
            "date": date_str,
            "message_id": payload.get("message_id"),
            "in_reply_to": payload.get("in_reply_to"),
            "references": payload.get("references"),
        }

        # Add optional fields
        if "cc" in payload:
            cc = payload["cc"]
            generic_email["cc"] = cc if isinstance(cc, list) else [cc]

        if "bcc" in payload:
            bcc = payload["bcc"]
            generic_email["bcc"] = bcc if isinstance(bcc, list) else [bcc]

        return generic_email

    def validate(self, payload: dict, headers: dict, secret: str) -> bool:
        """
        Validate webhook using custom header.

        For generic webhooks, we support simple token-based authentication
        via the X-Webhook-Token header.

        Args:
            payload: Webhook payload
            headers: HTTP headers
            secret: Expected token value

        Returns:
            True if token matches or no secret configured
        """
        if not secret:
            # No authentication required
            return True

        # Check for token in headers
        token = headers.get("X-Webhook-Token") or headers.get("x-webhook-token")

        if not token:
            return False

        # Simple string comparison (use HTTPS to protect token)
        import hmac
        return hmac.compare_digest(token, secret)
