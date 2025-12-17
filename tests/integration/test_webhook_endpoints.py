"""Integration tests for webhook endpoints."""

import hashlib
import hmac
import time
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Sample email payloads for different providers

SAMPLE_SENDGRID_PAYLOAD = {
    "from": "sender@example.com",
    "to": "support@company.com",
    "subject": "SendGrid Test Email",
    "text": "This is a test email from SendGrid.",
    "html": "<p>This is a test email from SendGrid.</p>",
    "headers": '{"Message-ID": "<test@sendgrid.com>", "Date": "2025-12-17T10:00:00Z"}',
    "envelope": '{"from": "sender@example.com", "to": ["support@company.com"]}',
}

SAMPLE_MAILGUN_PAYLOAD = {
    "sender": "sender@example.com",
    "recipient": "support@company.com",
    "subject": "Mailgun Test Email",
    "stripped-text": "This is a test email from Mailgun.",
    "body-html": "<p>This is a test email from Mailgun.</p>",
    "Message-Id": "<test@mailgun.com>",
    "timestamp": str(int(time.time())),
    "token": "test-token-123",
    "signature": "",  # Will be computed in test
}

SAMPLE_GENERIC_PAYLOAD = {
    "from": "sender@example.com",
    "to": ["support@company.com"],
    "subject": "Generic Test Email",
    "text": "This is a test email in generic format.",
    "html": "<p>This is a test email in generic format.</p>",
    "date": datetime.now().isoformat(),
    "message_id": "<test@generic.com>",
}


class TestSendGridWebhook:
    """Tests for SendGrid webhook endpoint."""

    @pytest.mark.asyncio
    async def test_receive_sendgrid_email_success(self, client: AsyncClient):
        """Test successful email reception from SendGrid."""
        response = await client.post(
            "/api/v1/webhooks/email/sendgrid",
            data=SAMPLE_SENDGRID_PAYLOAD,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["sender_email"] == "sender@example.com"
        assert data["subject"] == "SendGrid Test Email"
        assert "summary" in data
        assert "task_recommendations" in data

    @pytest.mark.asyncio
    async def test_receive_sendgrid_email_missing_from(self, client: AsyncClient):
        """Test SendGrid webhook with missing 'from' field."""
        invalid_payload = SAMPLE_SENDGRID_PAYLOAD.copy()
        del invalid_payload["from"]

        response = await client.post(
            "/api/v1/webhooks/email/sendgrid",
            data=invalid_payload,
        )

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]


class TestMailgunWebhook:
    """Tests for Mailgun webhook endpoint."""

    def _compute_mailgun_signature(self, payload: dict, secret: str) -> str:
        """Compute Mailgun webhook signature."""
        timestamp = payload["timestamp"]
        token = payload["token"]
        message = f"{timestamp}{token}".encode("utf-8")
        return hmac.new(
            key=secret.encode("utf-8"),
            msg=message,
            digestmod=hashlib.sha256,
        ).hexdigest()

    @pytest.mark.asyncio
    async def test_receive_mailgun_email_with_valid_signature(self, client: AsyncClient, monkeypatch):
        """Test Mailgun email reception with valid signature."""
        # Set webhook secret (in test environment, it's empty by default)
        # For this test, we'll use a test secret
        test_secret = "test-mailgun-secret"

        # Prepare payload with signature
        payload = SAMPLE_MAILGUN_PAYLOAD.copy()
        payload["signature"] = self._compute_mailgun_signature(payload, test_secret)

        # Use monkeypatch to temporarily set the secret
        from app.api.routers.webhooks import settings
        monkeypatch.setattr(settings, "mailgun_webhook_secret", test_secret)

        response = await client.post(
            "/api/v1/webhooks/email/mailgun",
            data=payload,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["sender_email"] == "sender@example.com"
        assert data["subject"] == "Mailgun Test Email"

    @pytest.mark.asyncio
    async def test_receive_mailgun_email_no_signature_validation_when_no_secret(
        self, client: AsyncClient
    ):
        """Test Mailgun accepts webhook when no secret is configured."""
        payload = SAMPLE_MAILGUN_PAYLOAD.copy()
        # Don't compute signature - should still work if no secret configured

        response = await client.post(
            "/api/v1/webhooks/email/mailgun",
            data=payload,
        )

        # Should succeed if no secret configured (relies on URL secrecy)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_receive_mailgun_email_invalid_signature(self, client: AsyncClient, monkeypatch):
        """Test Mailgun webhook with invalid signature."""
        test_secret = "test-mailgun-secret"

        # Prepare payload with WRONG signature
        payload = SAMPLE_MAILGUN_PAYLOAD.copy()
        payload["signature"] = "invalid-signature-xxx"

        from app.api.routers.webhooks import settings
        monkeypatch.setattr(settings, "mailgun_webhook_secret", test_secret)

        response = await client.post(
            "/api/v1/webhooks/email/mailgun",
            data=payload,
        )

        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]


class TestGenericWebhook:
    """Tests for generic webhook endpoint."""

    @pytest.mark.asyncio
    async def test_receive_generic_email_with_valid_token(self, client: AsyncClient, monkeypatch):
        """Test generic email reception with valid token."""
        test_token = "test-webhook-token-123"

        from app.api.routers.webhooks import settings
        monkeypatch.setattr(settings, "generic_webhook_secret", test_token)

        response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=SAMPLE_GENERIC_PAYLOAD,
            headers={"X-Webhook-Token": test_token},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["sender_email"] == "sender@example.com"
        assert data["subject"] == "Generic Test Email"
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_receive_generic_email_no_auth_when_no_secret(
        self, client: AsyncClient
    ):
        """Test generic webhook accepts email when no secret is configured."""
        response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=SAMPLE_GENERIC_PAYLOAD,
        )

        # Should succeed if no secret configured
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_receive_generic_email_missing_token(self, client: AsyncClient, monkeypatch):
        """Test generic webhook with missing authentication token."""
        test_token = "test-webhook-token-123"

        from app.api.routers.webhooks import settings
        monkeypatch.setattr(settings, "generic_webhook_secret", test_token)

        # No X-Webhook-Token header provided
        response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=SAMPLE_GENERIC_PAYLOAD,
        )

        assert response.status_code == 401
        assert "Invalid or missing X-Webhook-Token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_receive_generic_email_invalid_token(self, client: AsyncClient, monkeypatch):
        """Test generic webhook with wrong authentication token."""
        test_token = "test-webhook-token-123"

        from app.api.routers.webhooks import settings
        monkeypatch.setattr(settings, "generic_webhook_secret", test_token)

        response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=SAMPLE_GENERIC_PAYLOAD,
            headers={"X-Webhook-Token": "wrong-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_receive_generic_email_missing_required_fields(
        self, client: AsyncClient
    ):
        """Test generic webhook with missing required fields."""
        invalid_payload = {"subject": "Test"}  # Missing 'from' and 'to'

        response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=invalid_payload,
        )

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_receive_generic_email_invalid_json(self, client: AsyncClient):
        """Test generic webhook with invalid JSON payload."""
        response = await client.post(
            "/api/v1/webhooks/email/generic",
            content="not-valid-json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json()["detail"]


class TestWebhookEndToEnd:
    """End-to-end webhook workflow tests."""

    @pytest.mark.asyncio
    async def test_sendgrid_to_database_flow(self, client: AsyncClient):
        """Test complete SendGrid webhook flow: receive → process → store → retrieve."""
        # Step 1: Receive webhook
        create_response = await client.post(
            "/api/v1/webhooks/email/sendgrid",
            data=SAMPLE_SENDGRID_PAYLOAD,
        )
        assert create_response.status_code == 201
        intake_id = create_response.json()["id"]

        # Step 2: Retrieve stored intake
        get_response = await client.get(f"/api/v1/email-intakes/{intake_id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["sender_email"] == "sender@example.com"
        assert data["subject"] == "SendGrid Test Email"

    @pytest.mark.asyncio
    async def test_generic_webhook_with_decision_workflow(self, client: AsyncClient):
        """Test complete generic webhook flow including user decision."""
        # Step 1: Receive webhook
        create_response = await client.post(
            "/api/v1/webhooks/email/generic",
            json=SAMPLE_GENERIC_PAYLOAD,
        )
        assert create_response.status_code == 201
        intake_id = create_response.json()["id"]
        task_count = len(create_response.json()["task_recommendations"])

        # Step 2: Submit decision
        if task_count > 0:
            decision = {
                "approved_task_indices": [0],
                "approved_deal_indices": [],
            }
        else:
            decision = {
                "approved_task_indices": [],
                "approved_deal_indices": [],
            }

        decision_response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision",
            json=decision,
        )
        assert decision_response.status_code == 200
        assert decision_response.json()["status"] in ["user_approved", "rejected"]
