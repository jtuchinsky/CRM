"""Webhook API endpoints for receiving inbound emails."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.inbound.webhooks.generic_parser import GenericWebhookParser
from app.adapters.inbound.webhooks.mailgun_parser import MailgunWebhookParser
from app.adapters.inbound.webhooks.sendgrid_parser import SendGridWebhookParser
from app.adapters.outbound.db.sqlalchemy.session import get_db
from app.api.dependencies.intake_deps import get_process_email_use_case
from app.api.schemas.email_intake import IntakeDetailResponse
from app.core.application.use_cases.process_inbound_email import (
    ProcessInboundEmailUseCase,
)
from app.settings import get_settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@router.post(
    "/email/sendgrid",
    response_model=IntakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive email from SendGrid",
    description="Webhook endpoint for SendGrid Inbound Parse",
)
async def receive_sendgrid_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Receive and process email from SendGrid Inbound Parse webhook.

    SendGrid configuration:
    1. Go to Settings > Inbound Parse
    2. Add webhook URL: https://your-domain.com/api/v1/webhooks/email/sendgrid
    3. Configure domain/subdomain for receiving emails

    Args:
        request: FastAPI request object (contains form data)
        db: Database session

    Returns:
        IntakeDetailResponse with AI analysis

    Raises:
        HTTPException 400: If email format is invalid
        HTTPException 401: If webhook validation fails
        HTTPException 500: If processing fails
    """
    # Parse form data (SendGrid sends multipart/form-data)
    form = await request.form()
    payload = dict(form)

    # Get headers
    headers = dict(request.headers)

    # Initialize parser
    parser = SendGridWebhookParser()

    # Validate webhook (if secret is configured)
    secret = settings.sendgrid_webhook_secret
    if not parser.validate(payload, headers, secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        # Parse to generic format
        raw_email = parser.parse(payload, headers)

        # Process through intake pipeline
        use_case = get_process_email_use_case(db)
        intake_record = await use_case.execute(raw_email)

        # Convert to response format
        from app.api.routers.email_intake import _to_detail_response
        return _to_detail_response(intake_record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing failed: {str(e)}",
        )


@router.post(
    "/email/mailgun",
    response_model=IntakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive email from Mailgun",
    description="Webhook endpoint for Mailgun Routes",
)
async def receive_mailgun_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Receive and process email from Mailgun Routes webhook.

    Mailgun configuration:
    1. Go to Sending > Routes
    2. Create route with action: forward("https://your-domain.com/api/v1/webhooks/email/mailgun")
    3. Set priority and filter expression

    Args:
        request: FastAPI request object (contains form data)
        db: Database session

    Returns:
        IntakeDetailResponse with AI analysis

    Raises:
        HTTPException 400: If email format is invalid
        HTTPException 401: If webhook signature is invalid
        HTTPException 500: If processing fails
    """
    # Parse form data (Mailgun sends multipart/form-data)
    form = await request.form()
    payload = dict(form)

    # Get headers
    headers = dict(request.headers)

    # Initialize parser
    parser = MailgunWebhookParser()

    # Validate webhook signature (required for Mailgun)
    secret = settings.mailgun_webhook_secret
    if not parser.validate(payload, headers, secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        # Parse to generic format
        raw_email = parser.parse(payload, headers)

        # Process through intake pipeline
        use_case = get_process_email_use_case(db)
        intake_record = await use_case.execute(raw_email)

        # Convert to response format
        from app.api.routers.email_intake import _to_detail_response
        return _to_detail_response(intake_record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing failed: {str(e)}",
        )


@router.post(
    "/email/generic",
    response_model=IntakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive email (generic format)",
    description="Generic webhook endpoint for testing and custom integrations",
)
async def receive_generic_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> IntakeDetailResponse:
    """
    Receive and process email in generic format.

    This endpoint accepts emails in our standard format and is useful for:
    - Testing and development
    - Custom integrations
    - Internal email forwarding

    Authentication: Include X-Webhook-Token header matching GENERIC_WEBHOOK_SECRET

    Expected payload:
    ```json
    {
        "from": "sender@example.com",
        "to": ["recipient@example.com"],
        "subject": "Email subject",
        "text": "Plain text body",
        "html": "<p>HTML body</p>",
        "date": "2025-01-01T12:00:00Z",
        "message_id": "<unique-id@example.com>"
    }
    ```

    Args:
        request: FastAPI request object (contains JSON)
        db: Database session

    Returns:
        IntakeDetailResponse with AI analysis

    Raises:
        HTTPException 400: If email format is invalid
        HTTPException 401: If authentication fails
        HTTPException 500: If processing fails
    """
    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Get headers
    headers = dict(request.headers)

    # Initialize parser
    parser = GenericWebhookParser()

    # Validate webhook token
    secret = settings.generic_webhook_secret
    if not parser.validate(payload, headers, secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Webhook-Token header",
        )

    try:
        # Parse to generic format (pass-through with validation)
        raw_email = parser.parse(payload, headers)

        # Process through intake pipeline
        use_case = get_process_email_use_case(db)
        intake_record = await use_case.execute(raw_email)

        # Convert to response format
        from app.api.routers.email_intake import _to_detail_response
        return _to_detail_response(intake_record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing failed: {str(e)}",
        )
