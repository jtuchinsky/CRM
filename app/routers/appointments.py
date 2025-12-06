from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    appointment: AppointmentCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new appointment."""
    # Calculate end_time from start_time + duration
    end_time = appointment.start_time + timedelta(minutes=appointment.duration_minutes)

    db_appointment = Appointment(
        **appointment.model_dump(),
        end_time=end_time,
        status=AppointmentStatus.SCHEDULED.value,
    )
    db.add(db_appointment)
    await db.flush()
    await db.refresh(db_appointment)
    return db_appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """Get an appointment by ID."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    skip: int = 0,
    limit: int = 100,
    contact_id: int | None = None,
    staff_id: int | None = None,
    status: AppointmentStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all appointments with optional filters."""
    query = select(Appointment)

    if contact_id is not None:
        query = query.where(Appointment.contact_id == contact_id)

    if staff_id is not None:
        query = query.where(Appointment.staff_id == staff_id)

    if status is not None:
        query = query.where(Appointment.status == status.value)

    query = query.offset(skip).limit(limit).order_by(Appointment.start_time)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = appointment_update.model_dump(exclude_unset=True)

    # Recalculate end_time if start_time or duration changed
    if "start_time" in update_data or "duration_minutes" in update_data:
        start_time = update_data.get("start_time", appointment.start_time)
        duration = update_data.get("duration_minutes", appointment.duration_minutes)
        update_data["end_time"] = start_time + timedelta(minutes=duration)

    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.flush()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    await db.delete(appointment)
    return None
