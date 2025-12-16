"""API schemas for Email Intake endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# --- Request Schemas ---


class ProcessEmailRequest(BaseModel):
    """Request schema for processing a raw email."""

    raw_email: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "raw_email": {
                    "from": "customer@example.com",
                    "to": ["support@company.com"],
                    "subject": "Question about product pricing",
                    "text": "Hi, I'd like to know more about your enterprise pricing.",
                    "html": "<p>Hi, I'd like to know more about your enterprise pricing.</p>",
                    "date": "2025-12-16T10:30:00Z",
                    "message_id": "<abc123@mail.example.com>",
                }
            }
        }
    )


class SubmitDecisionRequest(BaseModel):
    """Request schema for submitting user decision on recommendations."""

    approved_task_indices: list[int] = []
    approved_deal_indices: list[int] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "approved_task_indices": [0, 1],
                "approved_deal_indices": [0],
            }
        }
    )


# --- Response Schemas ---


class TaskRecommendationResponse(BaseModel):
    """Task recommendation response."""

    title: str
    description: str
    priority: str
    due_date: str | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Follow up on pricing inquiry",
                "description": "Customer asked about enterprise pricing. Send detailed pricing sheet.",
                "priority": "high",
                "due_date": "2025-12-20",
            }
        }
    )


class DealRecommendationResponse(BaseModel):
    """Deal recommendation response."""

    contact_email: EmailStr
    deal_stage: str
    value: float
    notes: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contact_email": "customer@example.com",
                "deal_stage": "qualification",
                "value": 5000.0,
                "notes": "Enterprise pricing inquiry - potential high-value deal.",
            }
        }
    )


class EntityResponse(BaseModel):
    """Extracted entity response."""

    entity_type: str
    value: str
    confidence: float


class IntakeListResponse(BaseModel):
    """Simplified intake response for list views."""

    id: int
    status: str
    sender_email: EmailStr
    subject: str
    confidence_score: float
    intent: str
    summary: str
    task_count: int
    deal_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntakeDetailResponse(BaseModel):
    """Detailed intake response with full recommendations."""

    id: int
    status: str
    sender_email: EmailStr
    subject: str
    body_preview: str
    summary: str
    key_points: list[str]
    intent: str
    entities: list[EntityResponse]
    confidence_score: float
    confidence_reasoning: str
    task_recommendations: list[TaskRecommendationResponse]
    deal_recommendations: list[DealRecommendationResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "status": "pending_review",
                "sender_email": "customer@example.com",
                "subject": "Question about product pricing",
                "body_preview": "Hi, I'd like to know more about your enterprise pricing.",
                "summary": "Customer inquiry about enterprise pricing options.",
                "key_points": [
                    "Interested in enterprise pricing",
                    "Potential high-value customer",
                ],
                "intent": "inquiry",
                "entities": [
                    {
                        "entity_type": "ORGANIZATION",
                        "value": "Example Corp",
                        "confidence": 0.9,
                    }
                ],
                "confidence_score": 0.82,
                "confidence_reasoning": "Clear intent, specific request, identifiable entities.",
                "task_recommendations": [
                    {
                        "title": "Follow up on pricing inquiry",
                        "description": "Send enterprise pricing sheet",
                        "priority": "high",
                        "due_date": "2025-12-20",
                    }
                ],
                "deal_recommendations": [
                    {
                        "contact_email": "customer@example.com",
                        "deal_stage": "qualification",
                        "value": 5000.0,
                        "notes": "Enterprise pricing inquiry",
                    }
                ],
                "created_at": "2025-12-16T10:30:00",
                "updated_at": "2025-12-16T10:30:00",
            }
        },
    )


class IntakePaginationResponse(BaseModel):
    """Paginated list of intake records."""

    items: list[IntakeListResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
