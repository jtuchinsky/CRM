from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.outbound.db.sqlalchemy.session import Base, engine
from app.api.routers import appointments, contacts, email_intake, health, staff, webhooks
from app.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(contacts.router, prefix="/api/v1")
app.include_router(staff.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(email_intake.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "CRM API", "version": settings.app_version, "docs": "/docs"}
