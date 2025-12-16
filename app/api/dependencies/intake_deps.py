"""Dependency injection setup for Email Intake use cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.messaging.stub_event_bus import StubEventBus
from app.adapters.outbound.ai.llm_intake_engine import LLMIntakeEngine
from app.adapters.outbound.crm.context_lookup import CRMContextLookup
from app.adapters.outbound.db.repositories.intake_repository import IntakeRepository
from app.adapters.outbound.email.normalizer import EmailNormalizer
from app.adapters.outbound.providers.stub_pipeline_service import StubPipelineService
from app.adapters.outbound.providers.stub_task_service import StubTaskService
from app.core.application.use_cases.process_inbound_email import (
    ProcessInboundEmailUseCase,
)
from app.core.application.use_cases.submit_user_decision import (
    SubmitUserDecisionUseCase,
)


def get_process_email_use_case(db: AsyncSession) -> ProcessInboundEmailUseCase:
    """
    Construct ProcessInboundEmailUseCase with all dependencies.

    This function wires together:
    - Email normalizer (HTML cleaning, metadata extraction)
    - CRM context lookup (contact and interaction history)
    - AI intake engine (LLM-powered analysis)
    - Intake repository (persistence)
    - Event bus (domain event publishing)

    Args:
        db: SQLAlchemy async session

    Returns:
        ProcessInboundEmailUseCase ready to execute
    """
    normalizer = EmailNormalizer()
    crm_context = CRMContextLookup(db)
    ai_intake = LLMIntakeEngine()
    repository = IntakeRepository(db)
    event_bus = StubEventBus()

    return ProcessInboundEmailUseCase(
        normalizer=normalizer,
        crm_context=crm_context,
        ai_intake=ai_intake,
        repository=repository,
        event_bus=event_bus,
    )


def get_submit_decision_use_case(db: AsyncSession) -> SubmitUserDecisionUseCase:
    """
    Construct SubmitUserDecisionUseCase with all dependencies.

    This function wires together:
    - Intake repository (load intake, update decision)
    - Task service (create approved tasks - stub for now)
    - Pipeline service (create approved deals - stub for now)
    - Event bus (publish decision events)

    Args:
        db: SQLAlchemy async session

    Returns:
        SubmitUserDecisionUseCase ready to execute
    """
    repository = IntakeRepository(db)
    task_service = StubTaskService()
    pipeline_service = StubPipelineService()
    event_bus = StubEventBus()

    return SubmitUserDecisionUseCase(
        repository=repository,
        task_service=task_service,
        pipeline_service=pipeline_service,
        event_bus=event_bus,
    )
