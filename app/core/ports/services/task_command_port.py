"""Task command port - interface for task service operations."""

from abc import ABC, abstractmethod


class TaskCommandPort(ABC):
    """Port for creating tasks in task service (stub in Phase 1)."""

    @abstractmethod
    async def create_task(
        self,
        title: str,
        description: str,
        priority: str,
        due_date: str | None = None,
    ) -> dict:
        """
        Create a task in the task service.

        Args:
            title: Task title
            description: Task description
            priority: Priority level ("low", "medium", "high")
            due_date: Optional due date (ISO format)

        Returns:
            Created task dict with ID
            Example: {"id": 123, "title": "Follow up", "status": "created"}

        Raises:
            ValueError: If task creation fails
        """
        pass
