"""Unit tests for intake result domain entities."""

import pytest
from datetime import datetime

from app.core.domain.models.intake_result import (
    AIIntakeResult,
    IntakeDecision,
    IntakeRecord,
    Recommendations,
)
from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, ExtractedEntity, Intent, Summary
from app.core.domain.value_objects.email_metadata import EmailAddress, EmailBody, EmailHeaders
from app.core.domain.value_objects.recommendation import DealRecommendation, TaskRecommendation


class TestAIIntakeResult:
    """Test AIIntakeResult entity."""

    def create_sample_ai_result(self, confidence_score: float = 0.8) -> AIIntakeResult:
        """Helper to create sample AI result."""
        return AIIntakeResult(
            summary=Summary(
                text="Customer wants to schedule appointment",
                key_points=["Needs appointment", "Next week preferred"]
            ),
            intent=Intent.REQUEST,
            entities=[
                ExtractedEntity(entity_type="DATE", value="next week", confidence=0.9),
                ExtractedEntity(entity_type="PERSON", value="John", confidence=0.6),
            ],
            confidence=Confidence(
                overall_score=confidence_score,
                reasoning="Clear request with specific details"
            ),
        )

    def test_get_high_confidence_entities(self):
        """Test filtering entities by confidence."""
        result = self.create_sample_ai_result()
        high_conf = result.get_high_confidence_entities(threshold=0.7)
        assert len(high_conf) == 1
        assert high_conf[0].entity_type == "DATE"

    def test_has_high_confidence_true(self):
        """Test has_high_confidence() returns True for high score."""
        result = self.create_sample_ai_result(confidence_score=0.85)
        assert result.has_high_confidence(threshold=0.7) is True

    def test_has_high_confidence_false(self):
        """Test has_high_confidence() returns False for low score."""
        result = self.create_sample_ai_result(confidence_score=0.5)
        assert result.has_high_confidence(threshold=0.7) is False


class TestRecommendations:
    """Test Recommendations entity."""

    def test_has_recommendations_with_tasks(self):
        """Test has_recommendations() with tasks."""
        recs = Recommendations(
            tasks=[
                TaskRecommendation(
                    title="Follow up",
                    description="Contact customer",
                    priority="high"
                )
            ]
        )
        assert recs.has_recommendations() is True

    def test_has_recommendations_with_deals(self):
        """Test has_recommendations() with deals."""
        recs = Recommendations(
            deals=[
                DealRecommendation(
                    contact_email="john@example.com",
                    deal_stage="qualification",
                    value=1000.0,
                    notes="Interested in service"
                )
            ]
        )
        assert recs.has_recommendations() is True

    def test_has_recommendations_empty(self):
        """Test has_recommendations() with no recommendations."""
        recs = Recommendations()
        assert recs.has_recommendations() is False

    def test_count_total(self):
        """Test count_total() returns sum of tasks and deals."""
        recs = Recommendations(
            tasks=[
                TaskRecommendation(
                    title="Task 1",
                    description="Desc",
                    priority="low"
                )
            ],
            deals=[
                DealRecommendation(
                    contact_email="a@example.com",
                    deal_stage="stage",
                    value=100.0,
                    notes="Notes"
                ),
                DealRecommendation(
                    contact_email="b@example.com",
                    deal_stage="stage",
                    value=200.0,
                    notes="Notes"
                )
            ]
        )
        assert recs.count_total() == 3


class TestIntakeDecision:
    """Test IntakeDecision value object."""

    def test_has_approvals_true(self):
        """Test has_approvals() with approved tasks."""
        decision = IntakeDecision(approved_task_indices=[0, 1])
        assert decision.has_approvals() is True

    def test_has_approvals_with_deals(self):
        """Test has_approvals() with approved deals."""
        decision = IntakeDecision(approved_deal_indices=[0])
        assert decision.has_approvals() is True

    def test_has_approvals_false(self):
        """Test has_approvals() with no approvals."""
        decision = IntakeDecision(rejected_task_indices=[0])
        assert decision.has_approvals() is False


class TestIntakeRecord:
    """Test IntakeRecord aggregate root."""

    def create_sample_intake(self, confidence_score: float = 0.8) -> IntakeRecord:
        """Helper to create sample intake record."""
        email = NormalizedEmail(
            from_address=EmailAddress(email="customer@example.com", name="Customer"),
            to_addresses=[EmailAddress(email="support@company.com")],
            headers=EmailHeaders(
                subject="Need help",
                date=datetime(2025, 12, 15, 10, 0, 0),
                message_id="<msg123@example.com>"
            ),
            body=EmailBody(normalized_text="I need assistance"),
        )

        ai_result = AIIntakeResult(
            summary=Summary(
                text="Customer needs help",
                key_points=["Needs assistance"]
            ),
            intent=Intent.INQUIRY,
            entities=[],
            confidence=Confidence(
                overall_score=confidence_score,
                reasoning="Clear inquiry"
            ),
        )

        recommendations = Recommendations(
            tasks=[
                TaskRecommendation(
                    title="Respond to inquiry",
                    description="Help customer",
                    priority="medium"
                )
            ]
        )

        return IntakeRecord(
            normalized_email=email,
            ai_result=ai_result,
            recommendations=recommendations,
            status="pending_review",
            id=1,
        )

    def test_should_auto_approve_high_confidence(self):
        """Test should_auto_approve() returns True for high confidence."""
        intake = self.create_sample_intake(confidence_score=0.9)
        assert intake.should_auto_approve(threshold=0.85) is True

    def test_should_auto_approve_low_confidence(self):
        """Test should_auto_approve() returns False for low confidence."""
        intake = self.create_sample_intake(confidence_score=0.7)
        assert intake.should_auto_approve(threshold=0.85) is False

    def test_requires_human_review(self):
        """Test requires_human_review() is inverse of should_auto_approve()."""
        intake = self.create_sample_intake(confidence_score=0.7)
        assert intake.requires_human_review(threshold=0.85) is True
        assert intake.should_auto_approve(threshold=0.85) is False

    def test_is_decided_true(self):
        """Test is_decided() returns True when decision exists with approvals."""
        intake = self.create_sample_intake()
        intake.decision = IntakeDecision(approved_task_indices=[0])
        assert intake.is_decided() is True

    def test_is_decided_false_no_decision(self):
        """Test is_decided() returns False without decision."""
        intake = self.create_sample_intake()
        assert intake.is_decided() is False

    def test_get_sender_email(self):
        """Test get_sender_email() quick accessor."""
        intake = self.create_sample_intake()
        assert intake.get_sender_email() == "customer@example.com"

    def test_get_subject(self):
        """Test get_subject() quick accessor."""
        intake = self.create_sample_intake()
        assert intake.get_subject() == "Need help"

    def test_get_confidence_score(self):
        """Test get_confidence_score() quick accessor."""
        intake = self.create_sample_intake(confidence_score=0.75)
        assert intake.get_confidence_score() == 0.75
