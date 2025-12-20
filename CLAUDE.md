# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CRM (Customer Relationship Management) + AI Assistant system built with FastAPI, designed for small offices. The project follows **Clean Architecture** (Hexagonal/Ports & Adapters) principles with strict separation of concerns.

## Technology Stack

### Core Framework
- **Framework**: FastAPI 0.124.0+
- **Server**: Uvicorn 0.38.0 (async ASGI)
- **Database**: SQLAlchemy 2.0+ (async) with Alembic migrations
- **Validation**: Pydantic 2.12+ (v2 models)
- **Package Manager**: UV (modern Python dependency manager)
- **Python**: 3.12+
- **Testing**: pytest with pytest-asyncio

### AI & Email Processing
- **LLM Providers**: OpenAI (GPT-4o-mini) & Anthropic (Claude 3.5 Sonnet)
- **Email Parsing**: BeautifulSoup4 + lxml for HTML normalization
- **Retry Logic**: Tenacity with exponential backoff
- **Webhooks**: SendGrid, Mailgun, Generic (token-based)

## Architecture

### Clean Architecture Structure

The project follows Clean Architecture (Hexagonal/Ports & Adapters):

```
app/
├── main.py                       # FastAPI app + DI wiring
├── settings.py                   # Configuration (env vars)
├── api/                          # API Layer (Interface Adapters)
│   ├── routers/                  # HTTP controllers
│   └── schemas/                  # Pydantic request/response models
├── core/                         # Business Logic Layer
│   ├── domain/                   # Pure business entities
│   ├── ports/                    # Interfaces (dependency inversion)
│   └── application/              # Use cases / interactors
└── adapters/                     # Infrastructure Layer
    ├── inbound/                  # Webhooks, message handlers
    └── outbound/                 # DB, external APIs, queues
        └── db/sqlalchemy/        # SQLAlchemy ORM models
```

### Dependency Rule (CRITICAL)

**All dependencies must point INWARD toward business logic:**

- **Layer 1 (core/domain)**: NEVER imports from adapters, api, or external frameworks
- **Layer 2 (core/application)**: NEVER imports from adapters or api
- **Layer 3 (adapters/api)**: CAN import from core
- **Layer 4 (frameworks)**: CAN import from any layer

**Violations to Avoid:**
- ❌ Domain models importing SQLAlchemy or FastAPI
- ❌ Use cases directly using ORM models or HTTP types
- ❌ Business logic in controllers/routers
- ✅ Use dependency injection and port interfaces instead

See `docs/architecture.md` for detailed documentation.

### Key Architectural Patterns

**Ports & Adapters (Hexagonal Architecture):**
- **Ports**: Interfaces defined in `app/core/ports/` (repositories, services)
- **Inbound Adapters**: Webhooks in `app/adapters/inbound/` (email parsers)
- **Outbound Adapters**: External services in `app/adapters/outbound/` (AI, DB, email)

**Example: Email Intake Flow**
```
Webhook → Parser (inbound adapter) → Use Case →
  ├→ Normalizer (outbound adapter)
  ├→ AI Engine (outbound adapter)
  ├→ Repository (outbound adapter)
  └→ Event Bus (outbound adapter)
```

## Quick Reference

Most common commands for day-to-day development:

```bash
# Setup
uv sync                                          # Install dependencies
uv run alembic upgrade head                      # Apply migrations

# Development
uv run uvicorn main:app --reload                 # Run dev server
uv run pytest                                    # Run all tests
uv run pytest -v tests/integration/              # Run integration tests only
uv run pytest -v tests/unit/                     # Run unit tests only

# Database
uv run alembic revision --autogenerate -m "msg"  # Create migration
uv run alembic upgrade head                      # Apply migrations

# Code Quality
uv run black .                                   # Format code
uv run ruff check .                              # Lint code
```

## Development Commands

### Running the Application

```bash
# Run development server with auto-reload
uv run uvicorn main:app --reload

# Run on specific host/port
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Note:** The entry point is `main.py` in the project root directory, which imports the FastAPI app from `app/main.py`.

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs (Swagger)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_appointments.py

# Run only unit tests (business logic, mocked dependencies)
uv run pytest tests/unit/

# Run only integration tests (API endpoints, with test database)
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=app

# Run specific test by name pattern
uv run pytest -k "test_high_confidence"
```

### Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show current migration version
uv run alembic current
```

### Package Management (UV)

```bash
# Install dependencies
uv sync

# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# Remove a dependency
uv remove package-name
```

### Code Quality

```bash
# Format code with Black (line length: 100)
uv run black .

# Lint with Ruff
uv run ruff check .

# Type checking with mypy (strict mode)
uv run mypy app/
```

## Database

### Models (SQLAlchemy ORM)

Located in `app/adapters/outbound/db/sqlalchemy/`:
- `contact.py` - Contact information
- `staff.py` - Staff members
- `appointment.py` - Appointment scheduling
- `staff_availability.py` - Staff working hours and time off
- `reminder.py` - Appointment reminders
- `base.py` - Base mixins (IDMixin, TimestampMixin)

All models inherit from:
- `IDMixin`: Provides auto-incrementing `id` field
- `TimestampMixin`: Provides `created_at` and `updated_at` fields

### Session Management

Database session is managed in `app/adapters/outbound/db/sqlalchemy/session.py`:
- `Base`: SQLAlchemy declarative base
- `engine`: Async database engine (`create_async_engine`)
- `AsyncSessionLocal`: Session factory for async sessions
- `get_db()`: FastAPI dependency that yields database sessions with auto-commit/rollback

### Important Database Patterns

**ORM Model Registration for Migrations:**
- Models must be imported in `app/adapters/outbound/db/sqlalchemy/__init__.py`
- Models must be imported in `alembic/env.py` for Alembic to detect schema changes
- Use `lazy="selectin"` for relationships to avoid N+1 queries in async context

**JSON Serialization in ORM:**
- Use `JSON` column type for complex nested data (e.g., `IntakeRecord.ai_analysis`)
- SQLAlchemy automatically serializes/deserializes Python dicts to JSON

## Development Patterns

### Adding a New Feature

1. **Define domain logic** in `app/core/domain/models/` (pure Python)
2. **Create repository interface** in `app/core/ports/repositories/`
3. **Implement repository** in `app/adapters/outbound/db/sqlalchemy/`
4. **Create use case** in `app/core/application/use_cases/`
5. **Add Pydantic schemas** in `app/api/schemas/`
6. **Create router** in `app/api/routers/`
7. **Write tests** in `tests/`
8. **Create migration** with `uv run alembic revision --autogenerate`

### Adding a Database Model

1. Create SQLAlchemy model in `app/adapters/outbound/db/sqlalchemy/`
2. Import model in `app/adapters/outbound/db/sqlalchemy/__init__.py`
3. Import model in `alembic/env.py` for migration detection
4. Generate migration: `uv run alembic revision --autogenerate -m "Add model"`
5. Review and apply migration: `uv run alembic upgrade head`
6. Create corresponding Pydantic schemas in `app/api/schemas/`
7. Write tests

### Dependency Injection

**Database Session Injection:**
```python
from fastapi import Depends
from app.adapters.outbound.db.sqlalchemy.session import get_db

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    # Use db session
    pass
```

**Use Case Injection (for features with use cases):**
```python
# app/api/dependencies/intake_deps.py
from app.core.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from app.adapters.outbound.email.normalizer import EmailNormalizer
from app.adapters.outbound.ai.llm_intake_engine import LLMIntakeEngine
# ... other imports

def get_process_email_use_case(
    db: AsyncSession = Depends(get_db)
) -> ProcessInboundEmailUseCase:
    """Wire up dependencies for the use case"""
    normalizer = EmailNormalizer()
    ai_intake = LLMIntakeEngine()
    repository = IntakeRepository(db)
    event_bus = StubEventBus()

    return ProcessInboundEmailUseCase(
        normalizer=normalizer,
        ai_intake=ai_intake,
        repository=repository,
        event_bus=event_bus,
    )

# In router:
@router.post("/process")
async def process_email(
    use_case: ProcessInboundEmailUseCase = Depends(get_process_email_use_case)
):
    result = await use_case.execute(raw_email)
    return result
```

## Testing

### Test Layers

**1. Unit Tests** (Pure business logic, no database/HTTP):
```python
# tests/unit/use_cases/test_process_inbound_email.py
from unittest.mock import AsyncMock
import pytest

@pytest.mark.asyncio
async def test_high_confidence_auto_approved():
    """Test use case with mocked dependencies"""
    # Mock all port interfaces
    mock_normalizer = AsyncMock()
    mock_ai = AsyncMock()
    mock_ai.analyze.return_value = AIIntakeResult(confidence=0.90, ...)
    mock_repo = AsyncMock()
    mock_event_bus = AsyncMock()

    # Test pure business logic
    use_case = ProcessInboundEmailUseCase(
        normalizer=mock_normalizer,
        ai_intake=mock_ai,
        repository=mock_repo,
        event_bus=mock_event_bus
    )
    result = await use_case.execute(raw_email)

    # Verify behavior
    assert result.status == "auto_approved"
    mock_repo.save.assert_called_once()
```

**2. Integration Tests** (With database, test API endpoints):
```python
# tests/integration/test_appointments.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_appointment(client: AsyncClient):
    """Test API endpoint with test database"""
    response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": 1,
            "staff_id": 1,
            "start_time": "2025-12-15T09:00:00",
            "duration_minutes": 60,
            "title": "Annual Checkup"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Annual Checkup"
```

### Test Structure

- `tests/conftest.py` - Shared fixtures (test database, client)
- `tests/unit/` - Pure business logic tests (no DB/HTTP)
- `tests/integration/` - API endpoint tests (with test DB)
- All tests use `@pytest.mark.asyncio` decorator
- Test database: In-memory SQLite (`:memory:`) for speed

### Key Test Fixtures

- `test_db` - Creates test database with all tables, transaction rollback
- `client` - AsyncClient for making HTTP requests to test API
- `override_get_db` - Override database dependency for testing

## Environment Configuration

Configuration is managed in `app/settings.py` using pydantic-settings with LRU-cached singleton pattern.

### Example .env File

```bash
# Application
APP_NAME="CRM + AI Assistant"
APP_VERSION="0.1.0"
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./crm.db
DATABASE_ECHO=false

# AI / LLM (Email Intake Feature)
AI_PROVIDER=openai                      # "openai" or "anthropic"
AI_MODEL=gpt-4o-mini                   # or "claude-3-5-sonnet-20241022"
OPENAI_API_KEY=sk-...                  # Your OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...           # Your Anthropic API key

# Email Webhooks (for email reception)
SENDGRID_WEBHOOK_SECRET=               # Optional: custom header validation
MAILGUN_WEBHOOK_SECRET=                # Required: Mailgun API key for HMAC
GENERIC_WEBHOOK_SECRET=                # Required: Token for X-Webhook-Token
```

### Key Configuration Notes

- **AI Provider Switching**: Change `AI_PROVIDER` to switch between OpenAI and Anthropic
- **Auto-Approval Threshold**: Confidence >= 0.85 triggers auto-approval (hardcoded in `ConfidencePolicy`)
- **Webhook Security**: Each provider has different validation methods (HMAC, token-based)
- **Production DB**: Switch to `postgresql+asyncpg://...` for production

## Important Implementation Notes

### Async/Await Everywhere
- All routes, database operations, and external API calls use async/await
- Use `AsyncSession` for database operations, not sync `Session`
- Use `asyncio.gather()` for concurrent operations when appropriate

### Code Quality Configuration
- **Black**: Line length 100 characters
- **Ruff**: Line length 100 characters, target Python 3.12
- **MyPy**: Strict mode enabled (all type checking rules enforced)

### Current Architecture Status
- ✅ Clean Architecture directory structure implemented
- ✅ Ports & Adapters pattern for Email Intake feature
- ✅ Domain-driven design with use cases, policies, value objects
- ⚠️ Some older features (contacts, staff, appointments) still have business logic in routers
- ⚠️ Future refactoring: Extract use cases for CRUD features

### Email Intake Feature (Reference Implementation)
The Email Intake feature demonstrates the full Clean Architecture pattern:
- **Domain Models**: `IntakeRecord`, `NormalizedEmail`, `AIIntakeResult` (pure Python)
- **Use Cases**: `ProcessInboundEmailUseCase`, `SubmitUserDecisionUseCase`
- **Ports**: `EmailNormalizerPort`, `AIIntakePort`, `IntakeRepositoryPort`, `EventBusPort`
- **Adapters**: `EmailNormalizer`, `LLMIntakeEngine`, `IntakeRepository`, `SendGridWebhookParser`
- **Policies**: `ConfidencePolicy` (auto-approval threshold)

Use this as a reference when implementing new features.
