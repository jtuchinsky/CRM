"""Unit tests for SubmitUserDecisionUseCase."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from app.core.application.use_cases.submit_user_decision import SubmitUserDecisionUseCase
from app.core.domain.events import UserDecisionSubmitted
from app.core.domain.models.intake_result import AIIntakeResult, IntakeRecord, Recommendations
from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, Intent, Summary
from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.domain.value_objects.recommendation import DealRecommendation, TaskRecommendation


class TestSubmitUserDecisionUseCase:
    """Test SubmitUserDecisionUseCase with mocked dependencies."""

    def setup_method(self):
        """Setup mocks for each test."""
        # Create mock ports
        self.mock_repository = AsyncMock()
        self.mock_task_service = AsyncMock()
        self.mock_pipeline_service = AsyncMock()
        self.mock_event_bus = AsyncMock()

        # Create use case with mocked dependencies
        self.use_case = SubmitUserDecisionUseCase(
            repository=self.mock_repository,
            task_service=self.mock_task_service,
            pipeline_service=self.mock_pipeline_service,
            event_bus=self.mock_event_bus,
        )

    def create_sample_intake(self) -> IntakeRecord:
        """Helper to create sample intake record."""
        email = NormalizedEmail(
            from_address=EmailAddress(email="customer@example.com"),
            to_addresses=[EmailAddress(email="support@company.com")],
            headers=EmailHeaders(
                subject="Need help",
                date=datetime(2025, 12, 15, 10, 0, 0),
                message_id="<msg1@example.com>",
            ),
            body=EmailBody(normalized_text="Help needed"),
        )

        ai_result = AIIntakeResult(
            summary=Summary(text="Customer needs help", key_points=["Help"]),
            intent=Intent.INQUIRY,
            entities=[],
            confidence=Confidence(overall_score=0.8, reasoning="Clear"),
        )

        recommendations = Recommendations(
            tasks=[
                TaskRecommendation(
                    title="Follow up with customer",
                    description="Contact customer about inquiry",
                    priority="high",
                ),
                TaskRecommendation(
                    title="Research issue",
                    description="Investigate customer's concern",
                    priority="medium",
                ),
            ],
            deals=[
                DealRecommendation(
                    contact_email="customer@example.com",
                    deal_stage="qualification",
                    value=1000.0,
                    notes="Potential new deal",
                ),
            ],
        )

        return IntakeRecord(
            id=1,
            normalized_email=email,
            ai_result=ai_result,
            recommendations=recommendations,
            status="pending_review",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_execute_approve_single_task(self):
        """Test approving a single task."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_task_service.create_task.return_value = {
            "id": 101,
            "title": "Follow up with customer",
            "status": "created",
        }
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[0],  # Approve first task
            approved_deal_indices=[],
            decided_by="user@company.com",
        )

        # Assert
        self.mock_repository.get_by_id.assert_called_once_with(1)
        self.mock_task_service.create_task.assert_called_once_with(
            title="Follow up with customer",
            description="Contact customer about inquiry",
            priority="high",
            due_date=None,
        )
        self.mock_repository.update_decision.assert_called_once()

        # Verify event was published
        self.mock_event_bus.publish.assert_called_once()
        event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, UserDecisionSubmitted)
        assert event.intake_id == 1
        assert event.approved_task_count == 1
        assert event.approved_deal_count == 0
        assert event.decided_by == "user@company.com"

    @pytest.mark.asyncio
    async def test_execute_approve_multiple_tasks(self):
        """Test approving multiple tasks."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_task_service.create_task.side_effect = [
            {"id": 101, "status": "created"},
            {"id": 102, "status": "created"},
        ]
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[0, 1],  # Approve both tasks
            approved_deal_indices=[],
        )

        # Assert
        assert self.mock_task_service.create_task.call_count == 2

        # Verify first task creation
        first_call = self.mock_task_service.create_task.call_args_list[0]
        assert first_call[1]["title"] == "Follow up with customer"
        assert first_call[1]["priority"] == "high"

        # Verify second task creation
        second_call = self.mock_task_service.create_task.call_args_list[1]
        assert second_call[1]["title"] == "Research issue"
        assert second_call[1]["priority"] == "medium"

        # Verify event
        event = self.mock_event_bus.publish.call_args[0][0]
        assert event.approved_task_count == 2

    @pytest.mark.asyncio
    async def test_execute_approve_single_deal(self):
        """Test approving a single deal."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_pipeline_service.create_deal.return_value = {
            "id": 201,
            "contact_email": "customer@example.com",
            "status": "created",
        }
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[],
            approved_deal_indices=[0],  # Approve first deal
        )

        # Assert
        self.mock_pipeline_service.create_deal.assert_called_once_with(
            contact_email="customer@example.com",
            stage="qualification",
            value=1000.0,
            notes="Potential new deal",
        )

        # Verify event
        event = self.mock_event_bus.publish.call_args[0][0]
        assert event.approved_task_count == 0
        assert event.approved_deal_count == 1

    @pytest.mark.asyncio
    async def test_execute_approve_tasks_and_deals(self):
        """Test approving both tasks and deals."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_task_service.create_task.return_value = {"id": 101, "status": "created"}
        self.mock_pipeline_service.create_deal.return_value = {"id": 201, "status": "created"}
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[0],
            approved_deal_indices=[0],
            decided_by="admin@company.com",
        )

        # Assert
        self.mock_task_service.create_task.assert_called_once()
        self.mock_pipeline_service.create_deal.assert_called_once()

        # Verify event
        event = self.mock_event_bus.publish.call_args[0][0]
        assert event.approved_task_count == 1
        assert event.approved_deal_count == 1
        assert event.decided_by == "admin@company.com"

    @pytest.mark.asyncio
    async def test_execute_intake_not_found_raises_error(self):
        """Test that ValueError is raised when intake not found."""
        # Arrange
        self.mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Intake 999 not found"):
            await self.use_case.execute(
                intake_id=999,
                approved_task_indices=[],
                approved_deal_indices=[],
            )

        # Verify no services were called
        self.mock_task_service.create_task.assert_not_called()
        self.mock_pipeline_service.create_deal.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_task_index_raises_error(self):
        """Test that ValueError is raised for invalid task index."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake

        # Act & Assert - index 5 doesn't exist (only 0 and 1 are valid)
        with pytest.raises(ValueError, match="Invalid task index: 5"):
            await self.use_case.execute(
                intake_id=1,
                approved_task_indices=[5],
                approved_deal_indices=[],
            )

        # Verify no services were called
        self.mock_task_service.create_task.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_deal_index_raises_error(self):
        """Test that ValueError is raised for invalid deal index."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake

        # Act & Assert - index 3 doesn't exist (only 0 is valid)
        with pytest.raises(ValueError, match="Invalid deal index: 3"):
            await self.use_case.execute(
                intake_id=1,
                approved_task_indices=[],
                approved_deal_indices=[3],
            )

        # Verify no services were called
        self.mock_pipeline_service.create_deal.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_approve_nothing_still_succeeds(self):
        """Test that approving nothing (rejecting all) still works."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[],  # Approve nothing
            approved_deal_indices=[],  # Approve nothing
        )

        # Assert
        self.mock_task_service.create_task.assert_not_called()
        self.mock_pipeline_service.create_deal.assert_not_called()

        # Event should still be published with zero counts
        event = self.mock_event_bus.publish.call_args[0][0]
        assert event.approved_task_count == 0
        assert event.approved_deal_count == 0

    @pytest.mark.asyncio
    async def test_execute_updates_decision_with_correct_data(self):
        """Test that decision is updated with all relevant data."""
        # Arrange
        intake = self.create_sample_intake()
        self.mock_repository.get_by_id.return_value = intake
        self.mock_task_service.create_task.return_value = {"id": 101}
        self.mock_pipeline_service.create_deal.return_value = {"id": 201}
        self.mock_repository.update_decision.return_value = intake

        # Act
        result = await self.use_case.execute(
            intake_id=1,
            approved_task_indices=[0],
            approved_deal_indices=[0],
            decided_by="tester@company.com",
        )

        # Assert - verify decision object structure
        call_args = self.mock_repository.update_decision.call_args
        assert call_args[0][0] == 1  # intake_id
        decision = call_args[0][1]  # Now an IntakeDecision object, not dict

        assert decision.approved_task_indices == [0]
        assert decision.approved_deal_indices == [0]
        assert len(decision.created_tasks) == 1
        assert len(decision.created_deals) == 1
        assert decision.decided_by == "tester@company.com"
        assert decision.decided_at is not None
