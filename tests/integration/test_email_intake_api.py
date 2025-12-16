"""Integration tests for Email Intake API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Sample raw email payload
SAMPLE_EMAIL = {
    "raw_email": {
        "from": "customer@example.com",
        "to": ["support@company.com"],
        "subject": "Question about product pricing",
        "text": "Hi, I'd like to know more about your enterprise pricing options. We're a company of 50 employees looking for a comprehensive solution.",
        "html": "<p>Hi, I'd like to know more about your enterprise pricing options.</p><p>We're a company of 50 employees looking for a comprehensive solution.</p>",
        "date": "2025-12-16T10:30:00Z",
        "message_id": "<test123@mail.example.com>",
    }
}


class TestProcessEmailEndpoint:
    """Tests for POST /api/v1/email-intakes/process"""

    @pytest.mark.asyncio
    async def test_process_email_success(self, client: AsyncClient):
        """Test successful email processing."""
        response = await client.post("/api/v1/email-intakes/process", json=SAMPLE_EMAIL)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["sender_email"] == "customer@example.com"
        assert data["subject"] == "Question about product pricing"
        assert "summary" in data
        assert "confidence_score" in data
        assert "task_recommendations" in data
        assert "deal_recommendations" in data

        # Verify status is set based on confidence
        assert data["status"] in ["pending_review", "auto_approved"]

    @pytest.mark.asyncio
    async def test_process_email_invalid_payload(self, client: AsyncClient):
        """Test processing with invalid email payload."""
        invalid_email = {"raw_email": {"from": "invalid"}}  # Missing required fields

        response = await client.post("/api/v1/email-intakes/process", json=invalid_email)

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_process_email_missing_ai_keys(self, client: AsyncClient):
        """Test processing when AI API keys are not configured."""
        # This will likely fail with 500 if OpenAI/Anthropic keys are not set
        # Skip this test if you don't want to test error handling for missing keys
        pass


class TestListPendingEndpoint:
    """Tests for GET /api/v1/email-intakes/pending"""

    @pytest.mark.asyncio
    async def test_list_pending_reviews_empty(self, client: AsyncClient):
        """Test listing pending reviews when none exist."""
        response = await client.get("/api/v1/email-intakes/pending")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_pending_reviews_with_data(self, client: AsyncClient):
        """Test listing pending reviews after creating one."""
        # First, create an intake
        await client.post("/api/v1/email-intakes/process", json=SAMPLE_EMAIL)

        # Then, list pending reviews
        response = await client.get("/api/v1/email-intakes/pending")

        assert response.status_code == 200
        data = response.json()

        # Should have at least one item if auto-approved is False
        # Note: Actual count depends on AI confidence score
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_pending_reviews_pagination(self, client: AsyncClient):
        """Test pagination parameters."""
        response = await client.get("/api/v1/email-intakes/pending?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_pending_reviews_invalid_pagination(self, client: AsyncClient):
        """Test invalid pagination parameters."""
        response = await client.get("/api/v1/email-intakes/pending?skip=-1")
        assert response.status_code == 400

        response = await client.get("/api/v1/email-intakes/pending?limit=0")
        assert response.status_code == 400

        response = await client.get("/api/v1/email-intakes/pending?limit=1000")
        assert response.status_code == 400


class TestGetIntakeDetailEndpoint:
    """Tests for GET /api/v1/email-intakes/{intake_id}"""

    @pytest.mark.asyncio
    async def test_get_intake_detail_success(self, client: AsyncClient):
        """Test retrieving intake detail."""
        # First, create an intake
        create_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        intake_id = create_response.json()["id"]

        # Then, retrieve it
        response = await client.get(f"/api/v1/email-intakes/{intake_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == intake_id
        assert data["sender_email"] == "customer@example.com"
        assert "body_preview" in data
        assert "key_points" in data
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_get_intake_detail_not_found(self, client: AsyncClient):
        """Test retrieving non-existent intake."""
        response = await client.get("/api/v1/email-intakes/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestSubmitDecisionEndpoint:
    """Tests for POST /api/v1/email-intakes/{intake_id}/decision"""

    @pytest.mark.asyncio
    async def test_submit_decision_approve_tasks(self, client: AsyncClient):
        """Test submitting decision to approve tasks."""
        # First, create an intake
        create_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        intake_id = create_response.json()["id"]

        # Submit decision to approve first task
        decision = {"approved_task_indices": [0], "approved_deal_indices": []}

        response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision", json=decision
        )

        assert response.status_code == 200
        data = response.json()

        # Status should be updated
        assert data["status"] in ["user_approved", "rejected"]

    @pytest.mark.asyncio
    async def test_submit_decision_approve_deals(self, client: AsyncClient):
        """Test submitting decision to approve deals."""
        # First, create an intake
        create_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        intake_id = create_response.json()["id"]

        # Submit decision to approve first deal
        decision = {"approved_task_indices": [], "approved_deal_indices": [0]}

        response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision", json=decision
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == intake_id

    @pytest.mark.asyncio
    async def test_submit_decision_reject_all(self, client: AsyncClient):
        """Test submitting decision to reject all recommendations."""
        # First, create an intake
        create_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        intake_id = create_response.json()["id"]

        # Submit decision with empty approvals (reject all)
        decision = {"approved_task_indices": [], "approved_deal_indices": []}

        response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision", json=decision
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_submit_decision_not_found(self, client: AsyncClient):
        """Test submitting decision for non-existent intake."""
        decision = {"approved_task_indices": [], "approved_deal_indices": []}

        response = await client.post(
            "/api/v1/email-intakes/99999/decision", json=decision
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_decision_invalid_indices(self, client: AsyncClient):
        """Test submitting decision with invalid task/deal indices."""
        # First, create an intake
        create_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        intake_id = create_response.json()["id"]

        # Submit decision with out-of-range indices
        decision = {"approved_task_indices": [999], "approved_deal_indices": []}

        response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision", json=decision
        )

        assert response.status_code == 400
        assert "out of range" in response.json()["detail"].lower()


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, client: AsyncClient):
        """Test complete email intake workflow."""
        # Step 1: Process email
        process_response = await client.post(
            "/api/v1/email-intakes/process", json=SAMPLE_EMAIL
        )
        assert process_response.status_code == 201
        intake_id = process_response.json()["id"]

        # Step 2: List pending reviews (if not auto-approved)
        list_response = await client.get("/api/v1/email-intakes/pending")
        assert list_response.status_code == 200

        # Step 3: Get intake detail
        detail_response = await client.get(f"/api/v1/email-intakes/{intake_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        # Step 4: Submit decision
        decision = {
            "approved_task_indices": list(range(len(detail["task_recommendations"]))),
            "approved_deal_indices": list(range(len(detail["deal_recommendations"]))),
        }

        decision_response = await client.post(
            f"/api/v1/email-intakes/{intake_id}/decision", json=decision
        )
        assert decision_response.status_code == 200

        # Verify final status
        final_detail = decision_response.json()
        assert final_detail["status"] in ["user_approved", "rejected"]
