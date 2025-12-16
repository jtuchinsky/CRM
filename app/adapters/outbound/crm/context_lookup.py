"""CRM context lookup adapter - queries existing CRM data."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.outbound.db.sqlalchemy.appointment import Appointment
from app.adapters.outbound.db.sqlalchemy.contact import Contact
from app.core.ports.services.crm_context_port import CRMContextPort


class CRMContextLookup(CRMContextPort):
    """
    Looks up existing CRM data to enrich AI analysis.

    Queries:
    - Contact information by email
    - Recent appointments for the contact
    - (Future: deals, tasks, notes)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def lookup_contact_by_email(self, email: str) -> dict | None:
        """
        Find existing contact by email address.

        Args:
            email: Email address to search for

        Returns:
            Contact dict if found, None otherwise
            Example: {"id": 1, "name": "John Doe", "company": "Acme Corp"}
        """
        result = await self.db.execute(
            select(Contact).where(Contact.email == email.lower())
        )
        contact = result.scalar_one_or_none()

        if not contact:
            return None

        return {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "name": f"{contact.first_name} {contact.last_name}",
            "email": contact.email,
            "phone": contact.phone,
            "company": contact.company,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
        }

    async def get_recent_interactions(self, email: str, limit: int = 10) -> list[dict]:
        """
        Get recent interactions for this contact (appointments, tasks, deals).

        Currently only returns appointments. Tasks and deals to be added in Phase 7.

        Args:
            email: Contact email address
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dicts (appointments, tasks, etc.)
            Example: [{"type": "appointment", "date": "2025-12-10", "status": "completed"}]
        """
        # First, lookup contact
        result = await self.db.execute(
            select(Contact).where(Contact.email == email.lower())
        )
        contact = result.scalar_one_or_none()

        if not contact:
            return []

        # Get recent appointments for this contact
        appointment_result = await self.db.execute(
            select(Appointment)
            .where(Appointment.contact_id == contact.id)
            .order_by(Appointment.start_time.desc())
            .limit(limit)
        )
        appointments = appointment_result.scalars().all()

        interactions = []
        for appt in appointments:
            interactions.append({
                "type": "appointment",
                "id": appt.id,
                "title": appt.title,
                "status": appt.status,
                "start_time": appt.start_time.isoformat() if appt.start_time else None,
                "end_time": appt.end_time.isoformat() if appt.end_time else None,
                "description": appt.description,
                "location": appt.location,
            })

        # TODO Phase 7: Add task and deal lookups
        # task_result = await self.db.execute(...)
        # deal_result = await self.db.execute(...)

        return interactions
