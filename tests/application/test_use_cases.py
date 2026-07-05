from src.application.use_cases import (
    CompleteExecutionUseCase,
    EnqueueExecutionCommand,
    EnqueueExecutionUseCase,
    FailExecutionUseCase,
    StartExecutionUseCase,
)
from src.domain.events import DomainEvent
from src.domain.execution import ExecutionJob, ExecutionStatus


class InMemoryExecutionJobRepository:
    def __init__(self) -> None:
        self.items: dict[str, ExecutionJob] = {}

    def save(self, execution_job: ExecutionJob) -> None:
        self.items[execution_job.execution_id] = execution_job

    def get(self, execution_id: str) -> ExecutionJob:
        return self.items[execution_id]

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        return next(
            job
            for job in self.items.values()
            if job.service_order_id == service_order_id
        )


class EventCollector:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


def test_execution_happy_path_publishes_events_and_document_state() -> None:
    repository = InMemoryExecutionJobRepository()
    publisher = EventCollector()

    execution_job = EnqueueExecutionUseCase(repository, publisher).execute(
        EnqueueExecutionCommand("os-1")
    )
    StartExecutionUseCase(repository, publisher).execute(execution_job.execution_id)
    completed = CompleteExecutionUseCase(repository, publisher).execute(
        execution_job.execution_id,
        ["Diagnose brake noise", "Replace brake pads"],
    )

    assert completed.status == ExecutionStatus.COMPLETED
    assert completed.to_document()["status"] == "COMPLETED"
    assert [event.event_type for event in publisher.events] == [
        "EXECUTION_QUEUED",
        "EXECUTION_STARTED",
        "EXECUTION_COMPLETED",
    ]


def test_fail_execution_publishes_failure_event() -> None:
    repository = InMemoryExecutionJobRepository()
    publisher = EventCollector()
    execution_job = EnqueueExecutionUseCase(repository, publisher).execute(
        EnqueueExecutionCommand("os-1")
    )

    failed = FailExecutionUseCase(repository, publisher).execute(
        execution_job.execution_id, "Missing part"
    )

    assert failed.status == ExecutionStatus.FAILED
    assert failed.failure_reason == "Missing part"
    assert publisher.events[-1].event_type == "EXECUTION_FAILED"
