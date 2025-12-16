"""CRM context port - interface for looking up CRM data."""

from abc import ABC, abstractmethod


class CRMContextPort(ABC):
    """Port for retrieving CRM context to enrich AI analysis."""

    @abstractmethod
    async def lookup_contact_by_email(self, email: str) -> dict | None:
        """
        Find existing contact by email address.

        Args:
            email: Email address to search for

        Returns:
            Contact dict if found, None otherwise
            Example: {"id": 1, "name": "John Doe", "company": "Acme Corp"}
        """
        pass

    @abstractmethod
    async def get_recent_interactions(self, email: str, limit: int = 10) -> list[dict]:
        """
        Get recent interactions for this contact (appointments, tasks, deals).

        Args:
            email: Contact email address
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dicts (appointments, tasks, etc.)
            Example: [{"type": "appointment", "date": "2025-12-10", "status": "completed"}]
        """
        pass
