"""Unit tests for ProcessInboundEmailUseCase."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.core.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from app.core.domain.events import EmailIntakeProcessed
from app.core.domain.models.intake_result import AIIntakeResult, IntakeRecord, Recommendations
from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, Intent, Summary
from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.domain.value_objects.recommendation import TaskRecommendation


class TestProcessInboundEmailUseCase:
    """Test ProcessInboundEmailUseCase with mocked dependencies."""

    def setup_method(self):
        """Setup mocks for each test."""
        # Create mock ports
        self.mock_normalizer = AsyncMock()
        self.mock_crm_context = AsyncMock()
        self.mock_ai_intake = AsyncMock()
        self.mock_repository = AsyncMock()
        self.mock_event_bus = AsyncMock()

        # Create use case with mocked dependencies
        self.use_case = ProcessInboundEmailUseCase(
            normalizer=self.mock_normalizer,
            crm_context=self.mock_crm_context,
            ai_intake=self.mock_ai_intake,
            repository=self.mock_repository,
            event_bus=self.mock_event_bus,
        )

    def create_sample_normalized_email(self) -> NormalizedEmail:
        """Helper to create sample normalized email."""
        return NormalizedEmail(
            from_address=EmailAddress(email="customer@example.com", name="Customer"),
            to_addresses=[EmailAddress(email="support@company.com")],
            headers=EmailHeaders(
                subject="Need help with appointment",
                date=datetime(2025, 12, 15, 10, 0, 0),
                message_id="<msg123@example.com>",
            ),
            body=EmailBody(normalized_text="I need to schedule an appointment"),
        )

    def create_sample_ai_result(self, confidence_score: float = 0.8) -> AIIntakeResult:
        """Helper to create sample AI result."""
        return AIIntakeResult(
            summary=Summary(
                text="Customer wants to schedule appointment",
                key_points=["Needs appointment", "Urgent request"]
            ),
            intent=Intent.REQUEST,
            entities=[],
            confidence=Confidence(
                overall_score=confidence_score,
                reasoning="Clear request with specific details"
            ),
        )

    @pytest.mark.asyncio
    async def test_execute_high_confidence_auto_approved(self):
        """Test that high confidence (0.9) results in auto_approved status."""
        # Arrange
        raw_email = {"from": "customer@example.com", "subject": "Help"}
        normalized_email = self.create_sample_normalized_email()
        ai_result = self.create_sample_ai_result(confidence_score=0.9)

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = {"id": 1, "name": "Customer"}
        self.mock_crm_context.get_recent_interactions.return_value = []
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=1,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="auto_approved",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        result = await self.use_case.execute(raw_email)

        # Assert
        assert result.status == "auto_approved"
        assert result.id == 1

        # Verify normalizer was called
        self.mock_normalizer.normalize.assert_called_once_with(raw_email)

        # Verify CRM context lookup was called
        self.mock_crm_context.lookup_contact_by_email.assert_called_once_with("customer@example.com")
        self.mock_crm_context.get_recent_interactions.assert_called_once_with("customer@example.com")

        # Verify AI intake was called with context
        self.mock_ai_intake.analyze.assert_called_once()
        call_args = self.mock_ai_intake.analyze.call_args
        assert call_args[0][0] == normalized_email  # First arg is normalized email
        assert call_args[0][1]["is_existing_contact"] is True  # Context has contact

        # Verify repository save was called
        self.mock_repository.save.assert_called_once()
        saved_intake = self.mock_repository.save.call_args[0][0]
        assert saved_intake.status == "auto_approved"

        # Verify event was published
        self.mock_event_bus.publish.assert_called_once()
        event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, EmailIntakeProcessed)
        assert event.intake_id == 1
        assert event.status == "auto_approved"
        assert event.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_execute_low_confidence_pending_review(self):
        """Test that low confidence (0.7) results in pending_review status."""
        # Arrange
        raw_email = {"from": "customer@example.com", "subject": "Help"}
        normalized_email = self.create_sample_normalized_email()
        ai_result = self.create_sample_ai_result(confidence_score=0.7)

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = None  # No existing contact
        self.mock_crm_context.get_recent_interactions.return_value = []
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=2,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="pending_review",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        result = await self.use_case.execute(raw_email)

        # Assert
        assert result.status == "pending_review"
        assert result.id == 2

        # Verify context was set correctly for non-existing contact
        call_args = self.mock_ai_intake.analyze.call_args
        assert call_args[0][1]["is_existing_contact"] is False
        assert call_args[0][1]["contact"] is None

        # Verify event status
        event = self.mock_event_bus.publish.call_args[0][0]
        assert event.status == "pending_review"

    @pytest.mark.asyncio
    async def test_execute_with_existing_contact_and_interactions(self):
        """Test that existing contact data is passed to AI."""
        # Arrange
        raw_email = {"from": "john@example.com", "subject": "Follow up"}
        normalized_email = self.create_sample_normalized_email()
        normalized_email.from_address = EmailAddress(email="john@example.com", name="John")

        ai_result = self.create_sample_ai_result(confidence_score=0.8)

        contact = {"id": 5, "name": "John Doe", "company": "Acme Corp"}
        interactions = [
            {"type": "appointment", "date": "2025-12-10", "status": "completed"},
            {"type": "task", "title": "Follow up", "status": "done"},
        ]

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = contact
        self.mock_crm_context.get_recent_interactions.return_value = interactions
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=3,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="pending_review",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        result = await self.use_case.execute(raw_email)

        # Assert
        assert result.id == 3

        # Verify AI was given rich context
        call_args = self.mock_ai_intake.analyze.call_args
        context = call_args[0][1]
        assert context["is_existing_contact"] is True
        assert context["contact"] == contact
        assert context["recent_interactions"] == interactions
        assert len(context["recent_interactions"]) == 2

    @pytest.mark.asyncio
    async def test_execute_at_threshold_boundary_auto_approved(self):
        """Test confidence exactly at threshold (0.85) is auto-approved."""
        # Arrange
        raw_email = {"from": "test@example.com", "subject": "Test"}
        normalized_email = self.create_sample_normalized_email()
        ai_result = self.create_sample_ai_result(confidence_score=0.85)  # Exactly at threshold

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = None
        self.mock_crm_context.get_recent_interactions.return_value = []
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=4,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="auto_approved",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        result = await self.use_case.execute(raw_email)

        # Assert - should be auto_approved at exactly 0.85
        assert result.status == "auto_approved"

    @pytest.mark.asyncio
    async def test_execute_just_below_threshold_pending_review(self):
        """Test confidence just below threshold (0.84) is pending_review."""
        # Arrange
        raw_email = {"from": "test@example.com", "subject": "Test"}
        normalized_email = self.create_sample_normalized_email()
        ai_result = self.create_sample_ai_result(confidence_score=0.84)  # Just below threshold

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = None
        self.mock_crm_context.get_recent_interactions.return_value = []
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=5,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="pending_review",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        result = await self.use_case.execute(raw_email)

        # Assert - should be pending_review at 0.84
        assert result.status == "pending_review"

    @pytest.mark.asyncio
    async def test_execute_calls_all_dependencies_in_order(self):
        """Test that all dependencies are called in correct order."""
        # Arrange
        raw_email = {"from": "test@example.com"}
        normalized_email = self.create_sample_normalized_email()
        ai_result = self.create_sample_ai_result()

        # Setup mocks
        self.mock_normalizer.normalize.return_value = normalized_email
        self.mock_crm_context.lookup_contact_by_email.return_value = None
        self.mock_crm_context.get_recent_interactions.return_value = []
        self.mock_ai_intake.analyze.return_value = ai_result
        self.mock_repository.save.return_value = IntakeRecord(
            id=6,
            normalized_email=normalized_email,
            ai_result=ai_result,
            recommendations=Recommendations(),
            status="pending_review",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        await self.use_case.execute(raw_email)

        # Assert - verify call order
        self.mock_normalizer.normalize.assert_called_once()
        self.mock_crm_context.lookup_contact_by_email.assert_called_once()
        self.mock_crm_context.get_recent_interactions.assert_called_once()
        self.mock_ai_intake.analyze.assert_called_once()
        self.mock_repository.save.assert_called_once()
        self.mock_event_bus.publish.assert_called_once()
