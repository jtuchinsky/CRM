"""Process inbound email use case - orchestrates email intake workflow."""

from datetime import datetime

from app.core.domain.events import EmailIntakeProcessed
from app.core.domain.models.intake_result import IntakeRecord
from app.core.domain.policies.confidence_policy import ConfidencePolicy
from app.core.ports.repositories.intake_repository_port import IntakeRepositoryPort
from app.core.ports.services.ai_intake_port import AIIntakePort
from app.core.ports.services.crm_context_port import CRMContextPort
from app.core.ports.services.email_normalizer_port import EmailNormalizerPort
from app.core.ports.services.event_bus_port import EventBusPort


class ProcessInboundEmailUseCase:
    """
    Use case for processing inbound emails through AI intake pipeline.

    This orchestrates the complete workflow:
    1. Normalize email
    2. Lookup CRM context
    3. AI analysis
    4. Create intake record
    5. Persist
    6. Publish event
    """

    def __init__(
        self,
        normalizer: EmailNormalizerPort,
        crm_context: CRMContextPort,
        ai_intake: AIIntakePort,
        repository: IntakeRepositoryPort,
        event_bus: EventBusPort,
    ):
        """
        Initialize use case with dependencies.

        Args:
            normalizer: Email normalization service
            crm_context: CRM context lookup service
            ai_intake: AI analysis service
            repository: Intake persistence repository
            event_bus: Event publishing service
        """
        self.normalizer = normalizer
        self.crm_context = crm_context
        self.ai_intake = ai_intake
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, raw_email: dict) -> IntakeRecord:
        """
        Execute the email intake workflow.

        Args:
            raw_email: Raw email payload from webhook or manual input

        Returns:
            IntakeRecord with AI analysis and recommendations

        Raises:
            ValueError: If email processing fails
            RuntimeError: If a service is unavailable
        """
        # Step 1: Normalize email
        normalized = await self.normalizer.normalize(raw_email)

        # Step 2: Lookup CRM context for sender
        sender_email = normalized.from_address.email
        contact = await self.crm_context.lookup_contact_by_email(sender_email)
        interactions = await self.crm_context.get_recent_interactions(sender_email)

        context = {
            "contact": contact,
            "recent_interactions": interactions,
            "is_existing_contact": contact is not None,
        }

        # Step 3: AI analysis with context
        ai_result = await self.ai_intake.analyze(normalized, context)

        # Step 4: Extract recommendations (LLM adapter attaches them to ai_result)
        # LLM adapter adds recommendations as an attribute
        from app.core.domain.models.intake_result import Recommendations
        recommendations = getattr(ai_result, 'recommendations', Recommendations(tasks=[], deals=[]))

        # Step 5: Determine status based on confidence
        confidence_score = ai_result.confidence.overall_score
        status = (
            "auto_approved"
            if ConfidencePolicy.should_auto_approve(confidence_score)
            else "pending_review"
        )

        intake = IntakeRecord(
            normalized_email=normalized,
            ai_result=ai_result,
            recommendations=recommendations,
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Step 5: Persist to database
        saved = await self.repository.save(intake)

        # Step 6: Publish domain event
        event = EmailIntakeProcessed(
            intake_id=saved.id,
            timestamp=saved.created_at,
            confidence_score=confidence_score,
            sender_email=sender_email,
            subject=normalized.headers.subject,
            status=status,
        )
        await self.event_bus.publish(event)

        return saved
