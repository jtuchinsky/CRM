# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CRM (Customer Relationship Management) + AI Assistant system built with FastAPI, designed for small offices. The project follows **Clean Architecture** principles with clear separation of concerns.

## Technology Stack

- **Framework**: FastAPI 0.124.0+
- **Server**: Uvicorn 0.38.0 (async ASGI)
- **Database**: SQLAlchemy 2.0+ (async) with Alembic migrations
- **Validation**: Pydantic 2.12+
- **Package Manager**: UV (modern Python dependency manager)
- **Python**: 3.12+
- **Testing**: pytest with pytest-asyncio

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

### Dependency Rule

- **Inner layers** (core/domain) → NEVER depend on outer layers
- **Outer layers** (adapters) → CAN depend on inner layers
- **All dependencies** point inward toward business logic

See `docs/architecture.md` for detailed documentation.

## Development Commands

### Running the Application

```bash
# Run development server with auto-reload
uv run uvicorn main:app --reload

# Run on specific host/port
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

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

# Run with coverage
uv run pytest --cov=app
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
# Format code with Black
uv run black .

# Lint with Ruff
uv run ruff check .

# Type checking with mypy
uv run mypy app/
```

## Current API Endpoints

### Health Check
- `GET /health/` - Basic health check
- `GET /health/db` - Database connectivity check

### Contacts (v1)
- `POST /api/v1/contacts/` - Create contact
- `GET /api/v1/contacts/` - List contacts (pagination)
- `GET /api/v1/contacts/{id}` - Get contact by ID

### Staff (v1)
- `POST /api/v1/staff/` - Create staff member
- `GET /api/v1/staff/` - List staff (filter by active, role)
- `GET /api/v1/staff/{id}` - Get staff by ID
- `PATCH /api/v1/staff/{id}` - Update staff
- `DELETE /api/v1/staff/{id}` - Delete staff

### Appointments (v1)
- `POST /api/v1/appointments/` - Create appointment
- `GET /api/v1/appointments/` - List appointments (filter by contact, staff, status)
- `GET /api/v1/appointments/{id}` - Get appointment by ID
- `PATCH /api/v1/appointments/{id}` - Update appointment
- `DELETE /api/v1/appointments/{id}` - Delete appointment

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
- `engine`: Async database engine
- `AsyncSessionLocal`: Session factory
- `get_db()`: FastAPI dependency for database sessions

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

FastAPI's `Depends()` is used for dependency injection:

```python
from fastapi import Depends
from app.adapters.outbound.db.sqlalchemy.session import get_db

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    # Use db session
    pass
```

## Testing

### Test Structure

- `tests/conftest.py` - Shared fixtures (test database, client)
- `tests/test_*.py` - Test files organized by feature
- All tests use in-memory SQLite for fast execution

### Test Fixtures

- `test_db` - Creates test database with all tables
- `client` - AsyncClient for making HTTP requests to test API

### Writing Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient):
    response = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "John", "last_name": "Doe", "email": "john@example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
```

## Environment Configuration

Configuration is managed in `app/settings.py` using pydantic-settings:

```bash
# .env file
DATABASE_URL=sqlite+aiosqlite:///./crm.db
DATABASE_ECHO=false
APP_NAME="CRM + AI Assistant"
APP_VERSION="0.1.0"
```

## Documentation

- `README.md` - Project overview and setup instructions
- `docs/architecture.md` - Detailed architecture documentation
- `docs/C4.md` - C4 model diagrams (Context, Container, Component)
- `docs/BIG_PICTURE.md` - High-level system overview
- `test_main.http` - HTTP request examples for manual testing

## Development Notes

- The server runs on `http://127.0.0.1:8000` by default
- FastAPI provides automatic interactive API documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- All routes follow async/await patterns
- Database operations use SQLAlchemy 2.0 async API
- Tests run in parallel using pytest-asyncio
- UV manages dependencies in `pyproject.toml` (no requirements.txt)
