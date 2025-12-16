"""Submit user decision use case - handles user approval/rejection of recommendations."""

from datetime import datetime

from app.core.domain.events import UserDecisionSubmitted
from app.core.domain.models.intake_result import IntakeDecision, IntakeRecord
from app.core.ports.repositories.intake_repository_port import IntakeRepositoryPort
from app.core.ports.services.event_bus_port import EventBusPort
from app.core.ports.services.pipeline_command_port import PipelineCommandPort
from app.core.ports.services.task_command_port import TaskCommandPort


class SubmitUserDecisionUseCase:
    """
    Use case for submitting user decisions on AI recommendations.

    This orchestrates:
    1. Load intake record
    2. Create approved tasks
    3. Create approved deals
    4. Update intake status
    5. Publish event
    """

    def __init__(
        self,
        repository: IntakeRepositoryPort,
        task_service: TaskCommandPort,
        pipeline_service: PipelineCommandPort,
        event_bus: EventBusPort,
    ):
        """
        Initialize use case with dependencies.

        Args:
            repository: Intake persistence repository
            task_service: Task creation service
            pipeline_service: Deal creation service
            event_bus: Event publishing service
        """
        self.repository = repository
        self.task_service = task_service
        self.pipeline_service = pipeline_service
        self.event_bus = event_bus

    async def execute(
        self,
        intake_id: int,
        approved_task_indices: list[int],
        approved_deal_indices: list[int],
        decided_by: str | None = None,
    ) -> IntakeRecord:
        """
        Execute user decision submission workflow.

        Args:
            intake_id: Unique identifier of intake record
            approved_task_indices: Indices of approved task recommendations
            approved_deal_indices: Indices of approved deal recommendations
            decided_by: User ID or email who made the decision

        Returns:
            Updated IntakeRecord with decision

        Raises:
            ValueError: If intake not found or indices are invalid
        """
        # Step 1: Load intake record
        intake = await self.repository.get_by_id(intake_id)
        if not intake:
            raise ValueError(f"Intake {intake_id} not found")

        # Validate indices
        max_task_idx = len(intake.recommendations.tasks) - 1
        max_deal_idx = len(intake.recommendations.deals) - 1

        for idx in approved_task_indices:
            if idx < 0 or idx > max_task_idx:
                raise ValueError(f"Invalid task index: {idx}")

        for idx in approved_deal_indices:
            if idx < 0 or idx > max_deal_idx:
                raise ValueError(f"Invalid deal index: {idx}")

        # Step 2: Create approved tasks
        created_tasks = []
        for task_idx in approved_task_indices:
            task_rec = intake.recommendations.tasks[task_idx]
            created = await self.task_service.create_task(
                title=task_rec.title,
                description=task_rec.description,
                priority=task_rec.priority,
                due_date=task_rec.due_date,
            )
            created_tasks.append(created)

        # Step 3: Create approved deals
        created_deals = []
        for deal_idx in approved_deal_indices:
            deal_rec = intake.recommendations.deals[deal_idx]
            created = await self.pipeline_service.create_deal(
                contact_email=deal_rec.contact_email,
                stage=deal_rec.deal_stage,
                value=deal_rec.value,
                notes=deal_rec.notes,
            )
            created_deals.append(created)

        # Step 4: Update intake with decision
        decision = IntakeDecision(
            approved_task_indices=approved_task_indices,
            approved_deal_indices=approved_deal_indices,
            decided_at=datetime.now(),
            decided_by=decided_by,
        )

        decision_dict = {
            "approved_task_indices": approved_task_indices,
            "approved_deal_indices": approved_deal_indices,
            "created_tasks": created_tasks,
            "created_deals": created_deals,
            "decided_at": decision.decided_at.isoformat(),
            "decided_by": decided_by,
        }

        updated = await self.repository.update_decision(intake_id, decision_dict)

        # Step 5: Publish domain event
        event = UserDecisionSubmitted(
            intake_id=intake_id,
            timestamp=datetime.now(),
            approved_task_count=len(approved_task_indices),
            approved_deal_count=len(approved_deal_indices),
            decided_by=decided_by,
        )
        await self.event_bus.publish(event)

        return updated
