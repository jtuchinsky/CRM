"""Email Intake API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.outbound.db.repositories.intake_repository import IntakeRepository
from app.adapters.outbound.db.sqlalchemy.session import get_db
from app.api.dependencies.intake_deps import (
    get_process_email_use_case,
    get_submit_decision_use_case,
)
from app.api.schemas.email_intake import (
    EntityResponse,
    IntakeDetailResponse,
    IntakeListResponse,
    IntakePaginationResponse,
    ProcessEmailRequest,
    SubmitDecisionRequest,
    TaskRecommendationResponse,
    DealRecommendationResponse,
)
from app.core.application.use_cases.process_inbound_email import (
    ProcessInboundEmailUseCase,
)
from app.core.application.use_cases.submit_user_decision import (
    SubmitUserDecisionUseCase,
)
from app.core.domain.models.intake_result import IntakeRecord

router = APIRouter(prefix="/email-intakes", tags=["Email Intake"])


@router.post(
    "/process",
    response_model=IntakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process inbound email",
    description=(
        "Process a raw email through the AI intake pipeline. "
        "Returns analyzed email with AI recommendations for tasks and deals."
    ),
)
async def process_email(
    request: ProcessEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Process a raw email through the AI intake pipeline.

    This endpoint orchestrates the complete email intake workflow:
    1. Normalize email (clean HTML, extract metadata)
    2. Lookup CRM context (contact, recent interactions)
    3. AI analysis (summary, intent, entities, recommendations)
    4. Persist intake record
    5. Publish domain event

    Args:
        request: Raw email payload
        db: Database session

    Returns:
        IntakeDetailResponse with AI analysis and recommendations

    Raises:
        HTTPException 400: If email processing fails
        HTTPException 500: If AI service is unavailable
    """
    use_case = get_process_email_use_case(db)

    try:
        intake_record = await use_case.execute(request.raw_email)
        return _to_detail_response(intake_record)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {str(e)}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service unavailable: {str(e)}",
        )


@router.get(
    "/pending",
    response_model=IntakePaginationResponse,
    summary="List pending email intakes",
    description="Retrieve all email intakes pending human review, ordered by creation date (newest first).",
)
async def list_pending_reviews(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> IntakePaginationResponse:
    """
    List intake records pending human review.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 100)
        db: Database session

    Returns:
        IntakePaginationResponse with list of pending intakes

    Raises:
        HTTPException 400: If pagination parameters are invalid
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip must be >= 0",
        )
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100",
        )

    repository = IntakeRepository(db)
    intakes = await repository.list_pending_reviews(skip=skip, limit=limit)

    # Convert to list responses
    items = [_to_list_response(intake) for intake in intakes]

    # TODO: Add total count query for proper pagination
    # For now, return len(items) as approximation
    return IntakePaginationResponse(
        items=items,
        total=len(items),  # Approximation
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{intake_id}",
    response_model=IntakeDetailResponse,
    summary="Get intake details",
    description="Retrieve full details of a specific email intake record by ID.",
)
async def get_intake_detail(
    intake_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Get detailed intake record by ID.

    Args:
        intake_id: Primary key of intake record
        db: Database session

    Returns:
        IntakeDetailResponse with full details

    Raises:
        HTTPException 404: If intake record not found
    """
    repository = IntakeRepository(db)
    intake_record = await repository.get_by_id(intake_id)

    if not intake_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intake record not found: {intake_id}",
        )

    return _to_detail_response(intake_record)


@router.post(
    "/{intake_id}/decision",
    response_model=IntakeDetailResponse,
    summary="Submit user decision",
    description=(
        "Submit user decision on AI recommendations. "
        "Creates approved tasks and deals, updates intake status."
    ),
)
async def submit_decision(
    intake_id: int,
    request: SubmitDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Submit user decision on AI recommendations.

    This endpoint:
    1. Loads the intake record
    2. Creates approved tasks (via Task Service stub)
    3. Creates approved deals (via Pipeline Service stub)
    4. Updates intake status to 'user_approved' or 'rejected'
    5. Publishes UserDecisionSubmitted event

    Args:
        intake_id: Primary key of intake record
        request: User's decision (approved task/deal indices)
        db: Database session

    Returns:
        IntakeDetailResponse with updated status

    Raises:
        HTTPException 404: If intake record not found
        HTTPException 400: If invalid task/deal indices provided
    """
    use_case = get_submit_decision_use_case(db)

    try:
        updated_intake = await use_case.execute(
            intake_id=intake_id,
            approved_task_indices=request.approved_task_indices,
            approved_deal_indices=request.approved_deal_indices,
        )
        return _to_detail_response(updated_intake)
    except ValueError as e:
        # Check if it's a "not found" error or validation error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )


# --- Helper Functions ---


def _to_list_response(intake: IntakeRecord) -> IntakeListResponse:
    """Convert IntakeRecord to list response schema."""
    return IntakeListResponse(
        id=intake.id,
        status=intake.status,
        sender_email=intake.normalized_email.from_address.email,
        subject=intake.normalized_email.headers.subject,
        confidence_score=intake.ai_result.confidence.overall_score,
        intent=intake.ai_result.intent.value,
        summary=intake.ai_result.summary.text,
        task_count=len(intake.recommendations.tasks),
        deal_count=len(intake.recommendations.deals),
        created_at=intake.created_at,
        updated_at=intake.updated_at,
    )


def _to_detail_response(intake: IntakeRecord) -> IntakeDetailResponse:
    """Convert IntakeRecord to detail response schema."""
    # Get body preview (first 200 chars of normalized text)
    body_preview = intake.normalized_email.body.normalized_text[:200]
    if len(intake.normalized_email.body.normalized_text) > 200:
        body_preview += "..."

    # Convert entities
    entities = [
        EntityResponse(
            entity_type=entity.entity_type,
            value=entity.value,
            confidence=entity.confidence,
        )
        for entity in intake.ai_result.entities
    ]

    # Convert task recommendations
    tasks = [
        TaskRecommendationResponse(
            title=task.title,
            description=task.description,
            priority=task.priority,
            due_date=task.due_date,
        )
        for task in intake.recommendations.tasks
    ]

    # Convert deal recommendations
    deals = [
        DealRecommendationResponse(
            contact_email=deal.contact_email,
            deal_stage=deal.deal_stage,
            value=deal.value,
            notes=deal.notes,
        )
        for deal in intake.recommendations.deals
    ]

    return IntakeDetailResponse(
        id=intake.id,
        status=intake.status,
        sender_email=intake.normalized_email.from_address.email,
        subject=intake.normalized_email.headers.subject,
        body_preview=body_preview,
        summary=intake.ai_result.summary.text,
        key_points=intake.ai_result.summary.key_points,
        intent=intake.ai_result.intent.value,
        entities=entities,
        confidence_score=intake.ai_result.confidence.overall_score,
        confidence_reasoning=intake.ai_result.confidence.reasoning,
        task_recommendations=tasks,
        deal_recommendations=deals,
        created_at=intake.created_at,
        updated_at=intake.updated_at,
    )
