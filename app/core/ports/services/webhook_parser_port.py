"""Port interface for email webhook parsers."""

from abc import ABC, abstractmethod


class WebhookParserPort(ABC):
    """
    Abstract interface for parsing provider-specific email webhooks.

    Different email providers (SendGrid, Mailgun, Postmark, etc.) send
    webhooks with different formats. This port defines a standard interface
    for converting provider-specific payloads into a generic format.
    """

    @abstractmethod
    def parse(self, payload: dict, headers: dict) -> dict:
        """
        Parse provider-specific webhook payload into generic email format.

        Args:
            payload: Webhook payload body (JSON)
            headers: HTTP headers from webhook request

        Returns:
            Generic email dict with keys:
                - from: sender email (str)
                - to: recipient(s) (list[str] or str)
                - subject: email subject (str)
                - text: plain text body (optional)
                - html: HTML body (optional)
                - date: timestamp (ISO string)
                - message_id: unique message identifier
                - in_reply_to: replied message ID (optional)
                - references: list of message IDs (optional)

        Raises:
            ValueError: If payload format is invalid
        """
        pass

    @abstractmethod
    def validate(self, payload: dict, headers: dict, secret: str) -> bool:
        """
        Validate webhook authenticity using provider-specific verification.

        Args:
            payload: Webhook payload body
            headers: HTTP headers (may contain signature)
            secret: Shared secret/API key for validation

        Returns:
            True if webhook is authentic, False otherwise
        """
        pass
