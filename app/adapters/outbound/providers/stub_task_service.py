"""Stub task service adapter - logs task creation."""

import logging

from app.core.ports.services.task_command_port import TaskCommandPort

logger = logging.getLogger(__name__)


class StubTaskService(TaskCommandPort):
    """
    Stub implementation of TaskCommandPort that logs task creation.

    In production, this would call a real Task Service API or create tasks
    directly in the database. For MVP, we just log and return a fake ID.
    """

    _task_counter = 1000  # Start at 1000 for stub IDs

    async def create_task(
        self,
        title: str,
        description: str,
        priority: str,
        due_date: str | None = None,
    ) -> dict:
        """
        Log task creation and return stub task dict.

        Args:
            title: Task title
            description: Task description
            priority: Priority level ("low", "medium", "high")
            due_date: Optional due date (ISO format)

        Returns:
            Stub task dict with fake ID

        Raises:
            ValueError: Never raised in stub (always succeeds)
        """
        StubTaskService._task_counter += 1
        task_id = StubTaskService._task_counter

        logger.warning(
            f"⚠️  STUB: TaskService.create_task | "
            f"ID: {task_id} | "
            f"Title: {title} | "
            f"Priority: {priority} | "
            f"Due: {due_date or 'None'}"
        )

        return {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "status": "stub_created",
            "note": "This is a stub - task not actually created",
        }

        # TODO Phase 7: Replace with real Task Service implementation
