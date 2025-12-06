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
- **Package Manager**: UV
- **Python**: 3.12+

## Project Structure

```
CRM/
├── app/                          # Main application package
│   ├── config.py                 # Settings management
│   ├── database.py               # Database configuration
│   ├── main.py                   # FastAPI app instance
│   ├── models/                   # SQLAlchemy ORM models
│   ├── schemas/                  # Pydantic schemas
│   └── routers/                  # API route handlers
├── alembic/                      # Database migrations
├── tests/                        # Test suite
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

2. Install dependencies with UV:
```bash
uv sync
```

3. Copy the example environment file and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run database migrations:
```bash
uv run alembic upgrade head
```

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

This project follows a production-ready architecture with clear separation of concerns:

- **Models** (app/models/): SQLAlchemy ORM models defining database tables
- **Schemas** (app/schemas/): Pydantic models for request/response validation
- **Routers** (app/routers/): API endpoint handlers organized by domain
- **Database** (app/database.py): SQLAlchemy engine and session management

All models inherit from base mixins providing common fields (id, created_at, updated_at).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]
