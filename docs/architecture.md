# CRM System Architecture

## Overview

This CRM system follows **Clean Architecture** principles, ensuring separation of concerns, testability, and independence from frameworks and external systems.

## Clean Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRAMEWORKS & DRIVERS (Layer 4)                      │
│                         External Interfaces                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐             │
│  │   Web    │  │ Database │  │ External APIs│  │ Devices  │             │
│  │ REST API │  │ SQL/NoSQL│  │ 3rd Party    │  │ IoT      │             │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────┘             │
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐      │
│    │         INTERFACE ADAPTERS (Layer 3)                        │      │
│    │       Controllers, Presenters, Gateways                     │      │
│    │  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐   │      │
│    │  │Controllers │  │Presenters │  │ Gateways │  │  View   │   │
│    │  │  Handle    │  │  Format   │  │   Data   │  │ Models  │   │      │
│    │  │ Requests   │  │  Output   │  │  Access  │  │Transfer │   │      │
│    │  └────────────┘  └───────────┘  └──────────┘  └─────────┘   │      │
│    │                                                             │      │
│    │      ┌───────────────────────────────────────────────┐      │      │
│    │      │         USE CASES (Layer 2)                   │      │      │
│    │      │    Application Business Rules                 │      │      │
│    │      │  ┌──────────┐  ┌────────┐  ┌──────────────┐   │      │      │
│    │      │  │Interactors│ │ Input  │  │ Output       │   │      │      │
│    │      │  │ Business  │ │ Ports  │  │ Ports        │   │      │      │
│    │      │  │  Logic    │ └────────┘  └──────────────┘   │      │      │
│    │      │  └──────────┘                                 │      │      │
│    │      │  ┌──────────────────────────────────────┐     │      │      │
│    │      │  │      Orchestration / Workflow        │     │      │      │
│    │      │  └──────────────────────────────────────┘     │      │      │
│    │      │                                               │      │      │
│    │      │         ┌─────────────────────────┐           │      │      │
│    │      │         │   ENTITIES (Layer 1)    │           │      │      │
│    │      │         │  Enterprise Business    │           │      │      │
│    │      │         │        Rules            │           │      │      │
│    │      │         │  ┌─────────────────┐    │           │      │      │
│    │      │         │  │ Domain Models   │    │           │      │      │
│    │      │         │  │ Business Objects│    │           │      │      │
│    │      │         │  └─────────────────┘    │           │      │      │
│    │      │         └─────────────────────────┘           │      │      │
│    │      └───────────────────────────────────────────────┘      │      │
│    └─────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘

                    Dependencies point INWARD ──────>
```

## The Dependency Rule

**Critical Principle:** Source code dependencies must point only inward, toward higher-level policies.

- **Inner layers** know nothing about outer layers
- **Entities** don't know about Use Cases
- **Use Cases** don't know about Controllers
- **Controllers** don't know about Frameworks

## Layer Breakdown

### Layer 1: Entities (Enterprise Business Rules)

**Purpose:** Core business logic that is independent of any application

**Current State:** Currently implemented as SQLAlchemy ORM models (Layer 4 concern). Future refactoring will extract pure domain models here.

**Future Location in our CRM:**
- `app/core/domain/models/contact.py` - Pure Contact entity
- `app/core/domain/models/staff.py` - Pure Staff entity
- `app/core/domain/models/appointment.py` - Pure Appointment entity with business rules
- `app/core/domain/value_objects/email.py` - Email value object
- `app/core/domain/value_objects/phone.py` - Phone value object

**Current ORM Models (Infrastructure Layer):**
- `app/adapters/outbound/db/sqlalchemy/base.py` - Base mixins (IDMixin, TimestampMixin)
- `app/adapters/outbound/db/sqlalchemy/contact.py` - Contact ORM model
- `app/adapters/outbound/db/sqlalchemy/staff.py` - Staff ORM model
- `app/adapters/outbound/db/sqlalchemy/appointment.py` - Appointment ORM model
- `app/adapters/outbound/db/sqlalchemy/staff_availability.py` - Availability ORM model
- `app/adapters/outbound/db/sqlalchemy/reminder.py` - Reminder ORM model

**Characteristics:**
- Pure business objects (no framework dependencies)
- Can be used across multiple applications
- Encapsulate business-critical rules (e.g., AppointmentStatus enum)
- Independent of database implementation

**Example:**
```python
# Current (ORM coupled)
from app.adapters.outbound.db.sqlalchemy.appointment import AppointmentStatus

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Future (Pure domain entity)
# app/core/domain/models/appointment.py
class Appointment:
    def __init__(self, contact_id, staff_id, start_time, duration):
        self.contact_id = contact_id
        self.staff_id = staff_id
        self.start_time = start_time
        self.duration = duration
        self.status = AppointmentStatus.SCHEDULED

    def confirm(self) -> None:
        """Business rule: Can only confirm scheduled appointments"""
        if self.status != AppointmentStatus.SCHEDULED:
            raise ValueError("Can only confirm scheduled appointments")
        self.status = AppointmentStatus.CONFIRMED
```

### Layer 2: Use Cases (Application Business Rules)

**Purpose:** Application-specific business logic and orchestration

**Current State:** Planned but not yet implemented. Business logic currently lives in routers.

**Future Location in our CRM:**
- `app/core/application/use_cases/create_appointment.py` - Create appointment use case
- `app/core/application/use_cases/check_conflicts.py` - Conflict detection use case
- `app/core/application/use_cases/calculate_slots.py` - Available slot calculation
- `app/core/application/use_cases/manage_reminders.py` - Reminder creation logic
- `app/core/application/policies/identity_resolution.py` - Contact matching rules

**Ports (Interfaces):**
- `app/core/ports/repositories/appointment_repository.py` - Appointment repository interface
- `app/core/ports/repositories/staff_repository.py` - Staff repository interface
- `app/core/ports/services/email_provider.py` - Email service interface
- `app/core/ports/uow.py` - Unit of Work interface

**Characteristics:**
- Orchestrates flow of data to/from entities
- Implements application-specific business rules
- Independent of UI and database details
- Highly testable

**Example:**
```python
# Future use case implementation
# app/core/application/use_cases/check_conflicts.py
from app.core.ports.repositories.appointment_repository import AppointmentRepository
from app.core.domain.models.appointment import Appointment

class CheckConflictsUseCase:
    def __init__(self, appointment_repo: AppointmentRepository):
        self.appointment_repo = appointment_repo

    async def execute(
        self,
        staff_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Use case: Check if staff member has conflicting appointments"""
        existing = await self.appointment_repo.find_overlapping(
            staff_id, start_time, end_time
        )
        return len(existing) > 0
```

### Layer 3: Interface Adapters

**Purpose:** Convert data between Use Cases and external systems

**Location in our CRM:**

**Controllers (Routers):**
- `app/api/routers/contacts.py` - Contact API endpoints
- `app/api/routers/staff.py` - Staff API endpoints
- `app/api/routers/appointments.py` - Appointment API endpoints
- `app/api/routers/health.py` - Health check endpoints

**Presenters (Schemas):**
- `app/api/schemas/contact.py` - Contact data transfer objects
- `app/api/schemas/staff.py` - Staff DTOs
- `app/api/schemas/appointment.py` - Appointment DTOs with validation
- `app/api/schemas/staff_availability.py` - Availability DTOs

**Gateways (Future Repository Implementations):**
- `app/adapters/outbound/db/sqlalchemy/contact_repository.py` - Contact repository impl
- `app/adapters/outbound/db/sqlalchemy/appointment_repository.py` - Appointment repository impl
- `app/adapters/outbound/db/sqlalchemy/uow.py` - Unit of Work implementation
- `app/adapters/outbound/db/sqlalchemy/session.py` - Database session management

**Inbound Adapters (Future):**
- `app/adapters/inbound/email/gmail_webhook_handler.py` - Gmail webhook processing
- `app/adapters/messaging/queue_consumer.py` - Message queue consumer

**Characteristics:**
- Converts data formats (HTTP → Domain, Domain → Database)
- No business logic (only validation and transformation)
- Dependency Inversion: Uses interfaces/protocols

**Example:**
```python
# Current implementation
@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    appointment: AppointmentCreate,  # Input adapter
    db: AsyncSession = Depends(get_db)  # Gateway injection
):
    """Controller: Adapts HTTP request to domain logic"""
    # Calculate end_time from start_time + duration
    end_time = appointment.start_time + timedelta(minutes=appointment.duration_minutes)

    # Create ORM model (currently mixing layers)
    db_appointment = Appointment(**appointment.model_dump(), end_time=end_time)
    db.add(db_appointment)
    await db.flush()
    return db_appointment  # Returns AppointmentResponse (presenter)
```

### Layer 4: Frameworks & Drivers

**Purpose:** External tools and frameworks

**Location in our CRM:**
- **Web Framework:** FastAPI (`app/main.py`)
- **Database ORM:** SQLAlchemy (`app/adapters/outbound/db/sqlalchemy/*.py`)
- **Database Engine:** SQLite (dev) / PostgreSQL (prod)
- **Migration Tool:** Alembic (`alembic/`)
- **Configuration:** Pydantic Settings (`app/settings.py`)
- **Testing:** pytest + pytest-asyncio
- **Task Scheduler:** APScheduler (planned)
- **External APIs:** SendGrid, Twilio, Anthropic (planned)

**Characteristics:**
- Most volatile layer (easy to swap)
- Framework-specific code
- No business logic

## Current Project Structure

```
app/
├── main.py                          # FastAPI app + DI wiring
├── settings.py                      # Configuration (Pydantic Settings)
│
├── api/                             # Layer 3: Interface Adapters (Controllers & Presenters)
│   ├── routers/                     # HTTP controllers (FastAPI endpoints)
│   │   ├── contacts.py
│   │   ├── staff.py
│   │   ├── appointments.py
│   │   └── health.py
│   └── schemas/                     # Pydantic request/response models
│       ├── contact.py
│       ├── staff.py
│       ├── appointment.py
│       └── staff_availability.py
│
├── core/                            # Layer 1 & 2: Business Logic (Future)
│   ├── domain/                      # Layer 1: Pure domain entities
│   │   ├── models/                  # Domain models (no ORM)
│   │   └── value_objects/           # Immutable domain values
│   ├── ports/                       # Interfaces (dependency inversion)
│   │   ├── repositories/            # Repository interfaces
│   │   └── services/                # Service interfaces
│   └── application/                 # Layer 2: Use cases / interactors
│       ├── use_cases/               # Business use cases
│       ├── dto/                     # Data transfer objects
│       └── policies/                # Business policies/rules
│
└── adapters/                        # Layer 3 & 4: Infrastructure
    ├── inbound/                     # Inbound adapters
    │   └── email/                   # Email webhook handlers
    ├── outbound/                    # Outbound adapters
    │   ├── db/sqlalchemy/           # Database implementation (Layer 4)
    │   │   ├── session.py           # DB engine + session factory
    │   │   ├── base.py              # Base mixins (ID, Timestamp)
    │   │   ├── contact.py           # Contact ORM model
    │   │   ├── staff.py             # Staff ORM model
    │   │   ├── appointment.py       # Appointment ORM model
    │   │   ├── staff_availability.py
    │   │   └── reminder.py
    │   └── providers/               # External service adapters
    └── messaging/                   # Message queue adapters
```

## Data Flow

### Request Flow (Inward)

```
1. HTTP Request
   ↓
2. Router (Controller) - app/api/routers/appointments.py
   ↓
3. Schema Validation (Presenter) - app/api/schemas/appointment.py
   ↓
4. Use Case / Service - app/core/application/use_cases/ (Future)
   ↓
5. Domain Entity - app/core/domain/models/ (Future)
   ↓
6. Repository Interface - app/core/ports/repositories/
   ↓
7. Repository Implementation - app/adapters/outbound/db/sqlalchemy/
   ↓
8. SQLAlchemy ORM
   ↓
9. Database
```

### Response Flow (Outward)

```
1. Database
   ↓
2. SQLAlchemy ORM
   ↓
3. Repository Implementation - app/adapters/outbound/db/sqlalchemy/
   ↓
4. Domain Entity - app/core/domain/models/ (Future)
   ↓
5. Use Case Processing - app/core/application/use_cases/ (Future)
   ↓
6. Schema Transformation - app/api/schemas/appointment.py
   ↓
7. Router Response - app/api/routers/appointments.py
   ↓
8. HTTP Response (JSON)
```

## Dependency Inversion Principle (DIP)

### Problem Without DIP
```python
# BAD: High-level module depends on low-level module
class AppointmentService:
    def __init__(self):
        self.db = PostgreSQLDatabase()  # Direct dependency!
```

### Solution With DIP
```python
# GOOD: Both depend on abstraction
# app/core/ports/repositories/appointment_repository.py
class AppointmentRepository(Protocol):
    async def find_by_id(self, id: int) -> Appointment | None: ...
    async def save(self, appointment: Appointment) -> Appointment: ...

# app/core/application/use_cases/create_appointment.py
class CreateAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository):  # Abstraction
        self.repo = repo

# app/adapters/outbound/db/sqlalchemy/appointment_repository.py
class SQLAlchemyAppointmentRepository(AppointmentRepository):
    async def find_by_id(self, id: int) -> Appointment | None:
        # SQLAlchemy implementation
        pass

# FastAPI handles injection
async def create_appointment(
    use_case: CreateAppointmentUseCase = Depends(get_use_case)
):
    await use_case.execute(...)
```

## Key Benefits of This Architecture

### 1. Independent of Frameworks
- Can swap FastAPI → Flask → Django
- Business logic remains unchanged
- Only Layer 3 & 4 change

### 2. Testable
```python
# Test Use Cases without database or HTTP
async def test_conflict_detection():
    # Mock repository
    mock_repo = Mock(AppointmentRepository)
    use_case = CheckConflictsUseCase(mock_repo)

    # Test pure business logic
    # No FastAPI, no SQLAlchemy needed
    result = await use_case.execute(staff_id=1, ...)
    assert result is True
```

### 3. Independent of UI
- Same business logic for:
  - REST API
  - GraphQL
  - CLI
  - Web UI
  - gRPC

### 4. Independent of Database
```python
# Easy to switch: SQLite → PostgreSQL → MongoDB
# Only change: Repository implementations in app/adapters/outbound/
# Business logic in app/core/: unchanged
```

### 5. Screaming Architecture
```
app/
├── core/domain/models/   # "We handle Appointments and Staff!"
├── core/application/     # "We schedule things and manage contacts!"
├── api/routers/          # "We're an API!"
├── api/schemas/          # "We validate data!"
└── adapters/             # "We integrate with external systems!"
```
Directory structure tells you what the system does, not which framework it uses.

## CRM-Specific Architecture Mapping

### Contact Management Vertical
```
Layer 4: FastAPI + SQLAlchemy
         ↓
Layer 3: app/api/routers/contacts.py (Controller)
         app/api/schemas/contact.py (Presenter)
         app/adapters/outbound/db/sqlalchemy/contact.py (Gateway)
         ↓
Layer 2: CRUD operations (simple, no complex use cases yet)
         ↓
Layer 1: app/core/domain/models/contact.py (Future: Pure entity)
```

### Scheduling & Calendar Vertical
```
Layer 4: FastAPI + SQLAlchemy + APScheduler (planned)
         ↓
Layer 3: app/api/routers/appointments.py (Controller)
         app/api/routers/staff.py (Controller)
         app/api/schemas/appointment.py (Presenter)
         app/adapters/outbound/db/sqlalchemy/ (Gateways)
         ↓
Layer 2: app/core/application/use_cases/ (Planned)
         - check_conflicts.py (Conflict detection)
         - calculate_slots.py (Slot calculation)
         - manage_reminders.py (Reminder logic)
         ↓
Layer 1: app/core/domain/models/ (Planned)
         - appointment.py (Pure entity)
         - staff.py (Pure entity)
         - staff_availability.py (Pure entity)
```

## Testing Strategy by Layer

### Layer 1: Entity Tests
```python
# app/core/domain/models/appointment.py (Future)
def test_appointment_status_transitions():
    """Test business rules without database"""
    appt = Appointment(...)
    appt.confirm()
    assert appt.status == AppointmentStatus.CONFIRMED

    # Business rule: Can't cancel confirmed appointment
    with pytest.raises(ValueError):
        appt.cancel()
```

### Layer 2: Use Case Tests
```python
async def test_conflict_detection():
    """Test business logic with mocked repository"""
    mock_repo = Mock(AppointmentRepository)
    mock_repo.find_overlapping.return_value = [existing_appointment]

    use_case = CheckConflictsUseCase(mock_repo)
    has_conflict = await use_case.execute(staff_id=1, ...)

    assert has_conflict is True
    # No HTTP, no real database
```

### Layer 3: Integration Tests (Current)
```python
async def test_appointment_creation_endpoint(client: AsyncClient):
    """Test controller with test database"""
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

### Layer 4: E2E Tests
```python
async def test_full_appointment_workflow(client: AsyncClient):
    """Test entire system including database"""
    # Create staff
    staff = await client.post("/api/v1/staff/", json={...})

    # Create contact
    contact = await client.post("/api/v1/contacts/", json={...})

    # Create appointment
    appointment = await client.post("/api/v1/appointments/", json={...})

    # Verify in database
    assert appointment.status_code == 201
```

## Configuration Management

### Layered Configuration
```python
# Layer 4: Framework configuration
# app/settings.py - Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    app_name: str = "CRM + AI Assistant"
    # Framework-specific settings

# Layer 2: Business configuration (Future)
# app/core/application/config.py
class SchedulingConfig:
    max_appointment_duration: int = 480  # 8 hours
    default_buffer_minutes: int = 0
    allow_double_booking: bool = False
    # Business rules
```

## Evolution and Maintenance

### Adding New Features

**Example: Add Video Consultation Support**

1. **Layer 1:** Create `VideoConsultation` domain entity
   - `app/core/domain/models/video_consultation.py`

2. **Layer 2:** Create use cases
   - `app/core/application/use_cases/schedule_video_consultation.py`
   - `app/core/ports/services/video_provider.py` (interface)

3. **Layer 3:** Create adapters
   - `app/api/schemas/video_consultation.py` (Presenter)
   - `app/api/routers/video_consultations.py` (Controller)
   - `app/adapters/outbound/db/sqlalchemy/video_consultation.py` (Gateway)
   - `app/adapters/outbound/providers/zoom_client.py` (Implementation)

4. **Layer 4:** Integrate Zoom SDK
   - Add dependency: `uv add zoom-python-sdk`

**Benefits:** Clear separation, no "ripple effect" across layers

### Migrating Technologies

**Example: SQLite → PostgreSQL**

**Changes Required:**
- Layer 4: Database connection string in `.env`
- Layer 3: Minimal (if using SQLAlchemy properly)
- Layer 2: **No changes** ✓
- Layer 1: **No changes** ✓

**Example: FastAPI → Flask**

**Changes Required:**
- Layer 4: `app/main.py` (app initialization)
- Layer 3: `app/api/routers/*.py` (controller syntax)
- Layer 2: **No changes** ✓
- Layer 1: **No changes** ✓

## Anti-Patterns to Avoid

### ❌ Business Logic in Controllers
```python
# BAD: Business logic in Layer 3
@router.post("/appointments/")
async def create_appointment(data: dict, db: AsyncSession):
    # Checking conflicts here = business logic in controller!
    existing = await db.execute(
        select(Appointment).where(
            Appointment.staff_id == data["staff_id"],
            Appointment.start_time < data["end_time"],
            Appointment.end_time > data["start_time"]
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Conflict")
```

### ✅ Business Logic in Use Cases
```python
# GOOD: Business logic in Layer 2
@router.post("/appointments/")
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession,
    conflict_checker: CheckConflictsUseCase = Depends()
):
    # Delegate to use case
    if await conflict_checker.execute(db, data.staff_id, ...):
        raise HTTPException(status_code=409, detail="Conflict")
    # Create appointment...
```

### ❌ Entities Depending on Frameworks
```python
# BAD: Domain entity depends on FastAPI
from fastapi import HTTPException
from app.adapters.outbound.db.sqlalchemy.session import Base

class Appointment(Base):
    def validate(self):
        if self.duration > 480:
            raise HTTPException(...)  # Framework dependency in entity!
```

### ✅ Pure Entity Logic
```python
# GOOD: Pure domain entity
# app/core/domain/models/appointment.py
class Appointment:
    def validate(self) -> tuple[bool, str | None]:
        if self.duration > 480:
            return False, "Duration exceeds 8 hours"
        return True, None

# Validation happens in presenter (Layer 3)
# app/api/schemas/appointment.py
class AppointmentCreate(BaseModel):
    duration_minutes: int

    @field_validator("duration_minutes")
    def check_duration(cls, v):
        if v > 480:
            raise ValueError("Duration must not exceed 480 minutes")
        return v
```

### ❌ Use Cases Depending on ORM
```python
# BAD: Use case depends on SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.outbound.db.sqlalchemy.appointment import Appointment as ORMAppointment

class CreateAppointmentUseCase:
    async def execute(self, db: AsyncSession, data: dict):
        # Direct ORM usage in use case!
        appt = ORMAppointment(**data)
        db.add(appt)
```

### ✅ Use Cases Depending on Abstractions
```python
# GOOD: Use case depends on repository interface
from app.core.ports.repositories.appointment_repository import AppointmentRepository
from app.core.domain.models.appointment import Appointment

class CreateAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository):
        self.repo = repo

    async def execute(self, data: dict) -> Appointment:
        # Pure domain entity
        appointment = Appointment(**data)
        # Repository abstraction
        return await self.repo.save(appointment)
```

## Migration Path (Current → Clean Architecture)

### Current State (After Refactoring)
✅ Directory structure aligned with Clean Architecture
✅ Clear separation of API, Core, and Adapters layers
⚠️ ORM models still in adapters (not pure domain entities)
⚠️ Business logic in routers (not use cases)
⚠️ No repository abstractions (direct ORM usage)

### Phase 1: Extract Domain Entities (Next Step)
1. Create pure domain models in `app/core/domain/models/`
2. Keep ORM models in `app/adapters/outbound/db/sqlalchemy/`
3. Map between domain entities and ORM models

### Phase 2: Implement Repository Pattern
1. Define repository interfaces in `app/core/ports/repositories/`
2. Implement repositories in `app/adapters/outbound/db/sqlalchemy/`
3. Use dependency injection in controllers

### Phase 3: Extract Use Cases
1. Move business logic from routers to `app/core/application/use_cases/`
2. Controllers become thin adapters
3. Use cases depend on repository interfaces

### Phase 4: Complete Inversion
1. All dependencies point inward
2. Core has zero imports from adapters or API
3. Full Clean Architecture compliance

## Future Architecture Enhancements

### Phase 2: Advanced Scheduling
- Add CQRS (Command Query Responsibility Segregation)
- Separate read/write models for performance
- Event-driven appointment state changes

### Phase 3: Domain Events
- Event sourcing for audit trail
- Event-driven notification system
- Saga pattern for complex workflows

### Phase 4: Microservices (if needed)
- Each bounded context becomes independent service
- Clean Architecture makes extraction straightforward
- Shared domain models via published language

## Summary

This CRM system demonstrates Clean Architecture through:

1. **Clear Separation:** 4 distinct layers with defined responsibilities
2. **Dependency Rule:** Dependencies point inward toward business logic
3. **Testability:** Business logic can be tested independently
4. **Flexibility:** Easy to swap frameworks, databases, UIs
5. **Maintainability:** Changes localized to specific layers
6. **Evolutionary:** Structure supports gradual refinement

**The architecture "screams" CRM**, not FastAPI or SQLAlchemy. The system is about managing contacts, appointments, and staff—the frameworks are just implementation details that can be swapped.

### Current Implementation Status
- ✅ Directory structure follows Clean Architecture
- ✅ API layer properly separated
- ✅ Infrastructure adapters isolated
- ⚠️ Domain layer prepared but not yet populated
- ⚠️ Use cases to be extracted from controllers
- ⚠️ Repository pattern to be implemented

---

**Last Updated:** 2025-12-14
**Author:** Generated with Claude Code
**Version:** 2.0 (Post-Refactoring)
