# CRM + AI Assistant

A modern CRM system built with FastAPI, designed for small offices with AI-powered features.

## Features (MVP)

- Smart Contact Management
- Simple Pipeline (Leads → Active → Won)
- Email Sync + Unified Inbox
- AI Summaries & Intake Assistant
- Tasks & Follow-ups
- Calendar Sync
- Simple Invoicing
- Document Storage

## Technology Stack

- **Framework**: FastAPI 0.124.0+
- **Server**: Uvicorn with async support
- **Database**: SQLAlchemy 2.0+ (async)
- **Migrations**: Alembic
- **Validation**: Pydantic 2.12+
- **AI/LLM**: OpenAI & Anthropic APIs
- **Email Processing**: BeautifulSoup4, lxml
- **Retry Logic**: Tenacity
- **Package Manager**: UV
- **Python**: 3.12+

## Project Structure

This project follows **Clean Architecture** principles with clear separation of concerns:

```
CRM/
├── app/                          # Main application package
│   ├── main.py                   # FastAPI app instance + DI wiring
│   ├── settings.py               # App configuration and settings
│   ├── api/                      # API Layer (Interface Adapters)
│   │   ├── routers/              # HTTP controllers (endpoints)
│   │   │   ├── contacts.py
│   │   │   ├── staff.py
│   │   │   ├── appointments.py
│   │   │   ├── email_intake.py   # AI-powered email processing
│   │   │   └── health.py
│   │   ├── schemas/              # Pydantic models (API boundary)
│   │   │   ├── contact.py
│   │   │   ├── staff.py
│   │   │   ├── appointment.py
│   │   │   ├── email_intake.py
│   │   │   └── staff_availability.py
│   │   └── dependencies/         # Dependency injection
│   │       └── intake_deps.py    # Email intake DI wiring
│   ├── core/                     # Business Logic Layer
│   │   ├── domain/               # Enterprise business rules
│   │   │   ├── models/           # Domain entities (pure Python)
│   │   │   └── value_objects/    # Immutable domain values
│   │   ├── ports/                # Interfaces (dependency inversion)
│   │   │   ├── repositories/     # Repository interfaces
│   │   │   └── services/         # Service interfaces
│   │   └── application/          # Use cases / interactors
│   │       ├── use_cases/        # Business use cases
│   │       ├── dto/              # Data transfer objects
│   │       └── policies/         # Business policies/rules
│   └── adapters/                 # Infrastructure Layer
│       ├── inbound/              # Inbound adapters
│       │   └── email/            # Email webhook handlers
│       ├── outbound/             # Outbound adapters
│       │   ├── db/
│       │   │   ├── sqlalchemy/   # SQLAlchemy ORM implementation
│       │   │   │   ├── session.py    # DB engine + session factory
│       │   │   │   ├── base.py       # Base mixins (ID, Timestamp)
│       │   │   │   ├── email_intake.py  # Email intake ORM model
│       │   │   │   └── *.py          # Other ORM models
│       │   │   └── repositories/ # Repository implementations
│       │   │       └── intake_repository.py
│       │   ├── email/            # Email processing adapters
│       │   │   └── normalizer.py # Email cleaning & normalization
│       │   ├── ai/               # AI service adapters
│       │   │   └── llm_intake_engine.py  # OpenAI/Anthropic integration
│       │   ├── crm/              # CRM context adapters
│       │   │   └── context_lookup.py  # Contact/interaction lookup
│       │   └── providers/        # External service adapters (stubs)
│       │       ├── stub_task_service.py
│       │       └── stub_pipeline_service.py
│       └── messaging/            # Message queue adapters
│           └── stub_event_bus.py # Event publishing (stub)
├── alembic/                      # Database migrations
├── tests/                        # Test suite
├── docs/                         # Documentation
│   ├── architecture.md           # Architecture documentation
│   ├── C4.md                     # C4 model diagrams
│   └── BIG_PICTURE.md            # High-level system overview
├── main.py                       # Application entry point
├── pyproject.toml                # UV project configuration
└── .env                          # Environment variables (not in git)
```

## Setup

### Prerequisites

- Python 3.12+
- UV package manager ([installation instructions](https://github.com/astral-sh/uv))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jtuchinsky/CRM.git
cd CRM
```

1. Install dependencies with UV:
```bash
uv sync
```

1. Copy the example environment file and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

1. Run database migrations:
```bash
uv run alembic upgrade head
```

### AI Configuration (Email Intake Feature)

To enable the AI-powered Email Intake feature, configure your AI provider in `.env`:

```env
# AI / Email Intake
AI_PROVIDER=openai              # "openai" or "anthropic"
AI_MODEL=gpt-4o-mini            # or "claude-3-5-sonnet-20241022"
OPENAI_API_KEY=sk-...           # Your OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...    # Your Anthropic API key
```

**Features:**
- AI-powered email analysis (summary, intent classification, entity extraction)
- Automatic task and deal recommendations
- Confidence-based auto-approval (threshold: 0.85)
- Human review workflow for low-confidence emails

## Running the Application

### Development Server

```bash
# With UV
uv run uvicorn main:app --reload

# Or directly
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs (Swagger)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run with verbose output
uv run pytest -v
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

## API Endpoints

### Health Check
- `GET /health/` - Basic health check
- `GET /health/db` - Database connectivity check

### Contacts (v1)
- `POST /api/v1/contacts/` - Create a new contact
- `GET /api/v1/contacts/` - List all contacts (with pagination)
- `GET /api/v1/contacts/{id}` - Get a specific contact

### Staff (v1)
- `POST /api/v1/staff/` - Create a new staff member
- `GET /api/v1/staff/` - List all staff (filter by active status, role)
- `GET /api/v1/staff/{id}` - Get a specific staff member
- `PATCH /api/v1/staff/{id}` - Update staff details
- `DELETE /api/v1/staff/{id}` - Delete staff member

### Appointments (v1)
- `POST /api/v1/appointments/` - Create a new appointment
- `GET /api/v1/appointments/` - List appointments (filter by contact, staff, status)
- `GET /api/v1/appointments/{id}` - Get a specific appointment
- `PATCH /api/v1/appointments/{id}` - Update appointment details
- `DELETE /api/v1/appointments/{id}` - Delete appointment

### Email Intake (v1) - AI-Powered
- `POST /api/v1/email-intakes/process` - Process raw email through AI pipeline
- `GET /api/v1/email-intakes/pending` - List emails pending human review
- `GET /api/v1/email-intakes/{id}` - Get detailed intake analysis
- `POST /api/v1/email-intakes/{id}/decision` - Submit approval/rejection decision

## Database

### SQLite (Development)
The default configuration uses SQLite for easy development:
```env
DATABASE_URL=sqlite+aiosqlite:///./crm.db
```

### PostgreSQL (Production)
For production, use PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Development

### Adding Dependencies

```bash
# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Project Architecture

This project follows **Clean Architecture** (aka Hexagonal/Ports & Adapters) principles:

#### Layers (Dependency Rule: Inner → Outer)

1. **Core/Domain Layer** (`app/core/`)
   - **Domain Models**: Pure Python business entities (no framework dependencies)
   - **Value Objects**: Immutable domain values (Email, Phone, etc.)
   - **Ports**: Interfaces for repositories and services (dependency inversion)
   - **Use Cases**: Business logic orchestration (application layer)
   - **Policies**: Business rules and decision logic

2. **API Layer** (`app/api/`)
   - **Routers**: HTTP controllers (FastAPI endpoint handlers)
   - **Schemas**: Pydantic models for request/response validation (API boundary)
   - Handles HTTP concerns, authentication, and API versioning

3. **Adapters Layer** (`app/adapters/`)
   - **Inbound**: Webhooks, message handlers, scheduled jobs
   - **Outbound**: Database (SQLAlchemy ORM), external APIs, message queues
   - Implements interfaces defined in `core/ports/`

#### Key Principles

- **Dependency Inversion**: Core logic depends on abstractions (ports), not implementations
- **Single Responsibility**: Each layer has a clear purpose
- **Testability**: Business logic is isolated and easy to test
- **Flexibility**: Infrastructure can be swapped without changing business logic

See [`docs/architecture.md`](docs/architecture.md) for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]
