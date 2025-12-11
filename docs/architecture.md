# CRM System Architecture

## Overview

This CRM system follows **Clean Architecture** principles, ensuring separation of concerns, testability, and independence from frameworks and external systems.

## Clean Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRAMEWORKS & DRIVERS (Layer 4)                      │
│                         External Interfaces                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐          │
│  │   Web    │  │ Database │  │ External APIs│  │ Devices  │          │
│  │ REST API │  │ SQL/NoSQL│  │ 3rd Party    │  │ IoT      │          │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────┘          │
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐    │
│    │         INTERFACE ADAPTERS (Layer 3)                        │    │
│    │       Controllers, Presenters, Gateways                     │    │
│    │  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐ │    │
│    │  │Controllers │  │Presenters │  │ Gateways │  │  View   │ │    │
│    │  │  Handle    │  │  Format   │  │   Data   │  │ Models  │ │    │
│    │  │ Requests   │  │  Output   │  │  Access  │  │Transfer │ │    │
│    │  └────────────┘  └───────────┘  └──────────┘  └─────────┘ │    │
│    │                                                             │    │
│    │      ┌───────────────────────────────────────────────┐     │    │
│    │      │         USE CASES (Layer 2)                   │     │    │
│    │      │    Application Business Rules                 │     │    │
│    │      │  ┌──────────┐  ┌────────┐  ┌──────────────┐  │     │    │
│    │      │  │Interactors│ │ Input  │  │ Output       │  │     │    │
│    │      │  │ Business  │ │ Ports  │  │ Ports        │  │     │    │
│    │      │  │  Logic    │ └────────┘  └──────────────┘  │     │    │
│    │      │  └──────────┘                                 │     │    │
│    │      │  ┌──────────────────────────────────────┐    │     │    │
│    │      │  │      Orchestration / Workflow        │    │     │    │
│    │      │  └──────────────────────────────────────┘    │     │    │
│    │      │                                               │     │    │
│    │      │         ┌─────────────────────────┐          │     │    │
│    │      │         │   ENTITIES (Layer 1)    │          │     │    │
│    │      │         │  Enterprise Business    │          │     │    │
│    │      │         │        Rules            │          │     │    │
│    │      │         │  ┌─────────────────┐   │          │     │    │
│    │      │         │  │ Domain Models   │   │          │     │    │
│    │      │         │  │ Business Objects│   │          │     │    │
│    │      │         │  └─────────────────┘   │          │     │    │
│    │      │         └─────────────────────────┘          │     │    │
│    │      └───────────────────────────────────────────────┘     │    │
│    └─────────────────────────────────────────────────────────────┘    │
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

**Location in our CRM:**
- `app/models/base.py` - Base mixins (IDMixin, TimestampMixin)
- `app/models/contact.py` - Contact entity
- `app/models/staff.py` - Staff entity
- `app/models/appointment.py` - Appointment entity with business rules
- `app/models/staff_availability.py` - Availability entity
- `app/models/reminder.py` - Reminder entity

**Characteristics:**
- Pure business objects
- No dependencies on frameworks
- Can be used across multiple applications
- Encapsulate business-critical rules (e.g., AppointmentStatus enum)

**Example:**
```python
class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    # Business rule: Valid appointment states
```

### Layer 2: Use Cases (Application Business Rules)

**Purpose:** Application-specific business logic and orchestration

**Location in our CRM:**
- `app/services/scheduling.py` - Conflict detection use cases
- `app/services/slots.py` - Available slot calculation
- `app/services/reminder_manager.py` - Reminder creation logic
- `app/services/reminder_scheduler.py` - Background processing
- `app/services/ical.py` - Calendar export logic

**Characteristics:**
- Orchestrates flow of data to/from entities
- Implements application-specific business rules
- Independent of UI and database details
- Highly testable

**Example:**
```python
async def check_staff_conflict(
    db: AsyncSession,
    staff_id: int,
    start_time: datetime,
    end_time: datetime
) -> bool:
    """Use case: Check if staff member has conflicting appointments"""
    # Application business rule
    # Returns True if conflict exists
```

### Layer 3: Interface Adapters

**Purpose:** Convert data between Use Cases and external systems

**Location in our CRM:**

**Controllers (Routers):**
- `app/routers/contacts.py` - Contact API endpoints
- `app/routers/staff.py` - Staff API endpoints
- `app/routers/appointments.py` - Appointment API endpoints
- `app/routers/availability.py` - Availability API endpoints
- `app/routers/calendar.py` - Calendar export endpoints

**Presenters (Schemas):**
- `app/schemas/contact.py` - Contact data transfer objects
- `app/schemas/staff.py` - Staff DTOs
- `app/schemas/appointment.py` - Appointment DTOs with validation
- `app/schemas/staff_availability.py` - Availability DTOs

**Gateways:**
- `app/database.py` - Database session management
- `app/services/email.py` - Email gateway
- `app/services/sms.py` - SMS gateway

**Characteristics:**
- Converts data formats (HTTP → Domain, Domain → Database)
- No business logic (only validation and transformation)
- Dependency Inversion: Uses interfaces/protocols

**Example:**
```python
@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    appointment: AppointmentCreate,  # Input adapter
    db: AsyncSession = Depends(get_db)  # Gateway injection
):
    """Controller: Adapts HTTP request to use case"""
    # Transforms AppointmentCreate → Appointment entity
    # Invokes use case logic
    # Returns AppointmentResponse (presenter)
```

### Layer 4: Frameworks & Drivers

**Purpose:** External tools and frameworks

**Location in our CRM:**
- **Web Framework:** FastAPI (`app/main.py`)
- **Database:** SQLAlchemy + SQLite/PostgreSQL
- **Migration Tool:** Alembic (`alembic/`)
- **Task Scheduler:** APScheduler (future)
- **External APIs:** SendGrid, Twilio (future)

**Characteristics:**
- Most volatile layer (easy to swap)
- Framework-specific code
- No business logic

## Data Flow

### Request Flow (Inward)

```
1. HTTP Request
   ↓
2. Router (Controller) - app/routers/appointments.py
   ↓
3. Schema Validation (Presenter) - app/schemas/appointment.py
   ↓
4. Use Case / Service - app/services/scheduling.py
   ↓
5. Entity Manipulation - app/models/appointment.py
   ↓
6. Database Gateway - app/database.py
   ↓
7. SQLAlchemy ORM
   ↓
8. Database
```

### Response Flow (Outward)

```
1. Database
   ↓
2. SQLAlchemy ORM
   ↓
3. Entity Objects - app/models/appointment.py
   ↓
4. Use Case Processing - app/services/scheduling.py
   ↓
5. Schema Transformation - app/schemas/appointment.py
   ↓
6. Router Response - app/routers/appointments.py
   ↓
7. HTTP Response (JSON)
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
# GOOD: Both depend on abstraction (AsyncSession protocol)
class AppointmentService:
    def __init__(self, db: AsyncSession):  # Abstraction
        self.db = db

# Framework handles injection
async def create_appointment(
    db: AsyncSession = Depends(get_db)  # Injected!
):
    service = AppointmentService(db)
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
    # Mock database
    # Test pure business logic
    # No FastAPI needed
```

### 3. Independent of UI
- Same business logic for:
  - REST API
  - GraphQL
  - CLI
  - Web UI

### 4. Independent of Database
```python
# Easy to switch: SQLite → PostgreSQL → MongoDB
# Only change: app/database.py and alembic configs
# Business logic: unchanged
```

### 5. Screaming Architecture
```
app/
├── models/          # "We handle Appointments and Staff!"
├── routers/         # "We're an API!"
├── services/        # "We schedule things!"
└── schemas/         # "We validate data!"
```
Directory structure tells you what the system does, not which framework it uses.

## CRM-Specific Architecture Mapping

### Contact Management Vertical
```
Layer 4: FastAPI + SQLAlchemy
         ↓
Layer 3: app/routers/contacts.py (Controller)
         app/schemas/contact.py (Presenter)
         ↓
Layer 2: CRUD operations (simple, no complex use cases yet)
         ↓
Layer 1: app/models/contact.py (Entity)
```

### Scheduling & Calendar Vertical
```
Layer 4: FastAPI + APScheduler + iCalendar library
         ↓
Layer 3: app/routers/appointments.py (Controller)
         app/routers/availability.py (Controller)
         app/routers/calendar.py (Controller)
         app/schemas/appointment.py (Presenter)
         app/services/email.py (Gateway)
         ↓
Layer 2: app/services/scheduling.py (Conflict detection)
         app/services/slots.py (Slot calculation)
         app/services/reminder_manager.py (Reminder logic)
         app/services/ical.py (Calendar export)
         ↓
Layer 1: app/models/appointment.py (Entity)
         app/models/staff.py (Entity)
         app/models/staff_availability.py (Entity)
         app/models/reminder.py (Entity)
```

## Testing Strategy by Layer

### Layer 1: Entity Tests
```python
def test_appointment_status_enum():
    """Test business rules without database"""
    assert AppointmentStatus.SCHEDULED.value == "scheduled"
    assert AppointmentStatus.COMPLETED in AppointmentStatus
```

### Layer 2: Use Case Tests
```python
async def test_conflict_detection():
    """Test business logic with mocked database"""
    mock_db = Mock(AsyncSession)
    # Test conflict detection algorithm
    # No HTTP, no real database
```

### Layer 3: Integration Tests
```python
async def test_appointment_creation_endpoint():
    """Test controller with test database"""
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/v1/appointments/", json=data)
    assert response.status_code == 201
```

### Layer 4: E2E Tests
```python
def test_full_appointment_workflow():
    """Test entire system including database"""
    # Create staff
    # Create contact
    # Create appointment
    # Verify in database
```

## Configuration Management

### Layered Configuration
```python
# Layer 4: Framework configuration
# app/config.py - Pydantic Settings
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    # Framework-specific settings

# Layer 2: Business configuration
class SchedulingConfig:
    max_appointment_duration: int = 480
    default_buffer_minutes: int = 0
    # Business rules
```

## Evolution and Maintenance

### Adding New Features

**Example: Add Video Consultation**

1. **Layer 1:** Create `VideoConsultation` entity
2. **Layer 2:** Create `VideoService` use case
3. **Layer 3:** Create `VideoConsultationSchema` and router
4. **Layer 4:** Integrate Zoom/Teams SDK

**Benefits:** Clear separation, no "ripple effect"

### Migrating Technologies

**Example: PostgreSQL → MongoDB**

**Changes Required:**
- Layer 4: Database driver
- Layer 3: Gateway implementation (minimal)
- Layer 2: **No changes** ✓
- Layer 1: **No changes** ✓

## Anti-Patterns to Avoid

### ❌ Business Logic in Controllers
```python
# BAD
@router.post("/appointments/")
async def create_appointment(data: dict, db: AsyncSession):
    # Checking conflicts here = business logic in Layer 3!
    existing = await db.execute(...)
    if existing:
        raise HTTPException(...)
```

### ✅ Business Logic in Use Cases
```python
# GOOD
@router.post("/appointments/")
async def create_appointment(data: AppointmentCreate, db: AsyncSession):
    # Delegate to use case
    if await scheduling_service.check_conflict(db, ...):
        raise HTTPException(...)
```

### ❌ Entities Depending on Frameworks
```python
# BAD
from fastapi import HTTPException

class Appointment(Base):
    def validate(self):
        if self.duration > 480:
            raise HTTPException(...)  # Framework dependency!
```

### ✅ Pure Entity Logic
```python
# GOOD
class Appointment(Base):
    def validate(self) -> bool:
        return self.duration <= 480  # Pure logic

# Validation happens in schema (Layer 3)
class AppointmentCreate(BaseModel):
    @field_validator("duration_minutes")
    def check_duration(cls, v):
        if v > 480:
            raise ValueError(...)  # Presenter's job
```

## Future Architecture Enhancements

### Phase 2: Advanced Scheduling
- Add CQRS (Command Query Responsibility Segregation)
- Separate read/write models for performance

### Phase 3: Event-Driven Architecture
- Domain events for appointment state changes
- Event sourcing for audit trail

### Phase 4: Microservices (if needed)
- Each vertical becomes independent service
- Clean Architecture makes extraction easy

## Summary

This CRM system demonstrates Clean Architecture through:

1. **Clear Separation:** 4 distinct layers with defined responsibilities
2. **Dependency Rule:** All dependencies point inward
3. **Testability:** Business logic isolated from infrastructure
4. **Flexibility:** Easy to swap frameworks, databases, UIs
5. **Maintainability:** Changes localized to specific layers

**The architecture "screams" CRM**, not FastAPI or SQLAlchemy. The system is about managing contacts, appointments, and staff—the frameworks are just implementation details.

---

**Last Updated:** 2025-12-06
**Author:** Generated with Claude Code
**Version:** 1.0
