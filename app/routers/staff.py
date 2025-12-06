from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.post("/", response_model=StaffResponse, status_code=201)
async def create_staff(staff: StaffCreate, db: AsyncSession = Depends(get_db)):
    """Create a new staff member."""
    db_staff = Staff(**staff.model_dump())
    db.add(db_staff)
    await db.flush()
    await db.refresh(db_staff)
    return db_staff


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    """Get a staff member by ID."""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


@router.get("/", response_model=list[StaffResponse])
async def list_staff(
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all staff members with optional filters."""
    query = select(Staff)

    if is_active is not None:
        query = query.where(Staff.is_active == is_active)

    if role is not None:
        query = query.where(Staff.role == role)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int, staff_update: StaffUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a staff member."""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    update_data = staff_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)

    await db.flush()
    await db.refresh(staff)
    return staff


@router.delete("/{staff_id}", status_code=204)
async def delete_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a staff member."""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    await db.delete(staff)
    return None
