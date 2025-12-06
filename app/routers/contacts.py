from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contact."""
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    await db.flush()
    await db.refresh(db_contact)
    return db_contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Get a contact by ID."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.get("/", response_model=list[ContactResponse])
async def list_contacts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all contacts."""
    result = await db.execute(select(Contact).offset(skip).limit(limit))
    return result.scalars().all()
