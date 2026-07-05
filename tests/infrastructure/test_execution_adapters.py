import pytest

from src.application.use_cases import (
    CompleteExecutionUseCase,
    EnqueueExecutionCommand,
    EnqueueExecutionUseCase,
    StartExecutionUseCase,
)
from src.domain.events import DomainEvent
from src.domain.execution import ExecutionJob, ExecutionStatus
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.repositories.in_memory_execution_repository import (
    InMemoryExecutionJobRepository,
)
from src.infrastructure.repositories.mongo_execution_repository import (
    MongoExecutionJobRepository,
)


class FakeMongoCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, object]] = {}

    def replace_one(
        self,
        filter: dict[str, object],
        replacement: dict[str, object],
        upsert: bool = False,
    ) -> None:
        assert upsert is True
        self.documents[str(filter["execution_id"])] = replacement

    def find_one(self, filter: dict[str, object]) -> dict[str, object] | None:
        if "execution_id" in filter:
            return self.documents.get(str(filter["execution_id"]))
        service_order_id = str(filter["service_order_id"])
        return next(
            (
                document
                for document in self.documents.values()
                if document["service_order_id"] == service_order_id
            ),
            None,
        )


def test_in_memory_adapters_support_execution_happy_path() -> None:
    repository = InMemoryExecutionJobRepository()
    publisher = InMemoryEventPublisher()

    execution_job = EnqueueExecutionUseCase(repository, publisher).execute(
        EnqueueExecutionCommand("os-1")
    )
    StartExecutionUseCase(repository, publisher).execute(execution_job.execution_id)
    completed = CompleteExecutionUseCase(repository, publisher).execute(
        execution_job.execution_id,
        ["Diagnose brake noise"],
    )

    assert repository.get_by_service_order_id("os-1") is execution_job
    assert completed.status == ExecutionStatus.COMPLETED
    assert [event.event_type for event in publisher.events] == [
        "EXECUTION_QUEUED",
        "EXECUTION_STARTED",
        "EXECUTION_COMPLETED",
    ]


def test_in_memory_repository_raises_clear_errors_when_missing() -> None:
    repository = InMemoryExecutionJobRepository()

    with pytest.raises(KeyError, match="Execution job not found"):
        repository.get("missing")
    with pytest.raises(KeyError, match="Execution job not found for service order"):
        repository.get_by_service_order_id("missing")


def test_mongo_repository_saves_and_restores_execution_document() -> None:
    collection = FakeMongoCollection()
    repository = MongoExecutionJobRepository(collection)
    execution_job, _ = ExecutionJob.enqueue("os-1")
    execution_job.start()
    execution_job.add_step("Diagnose brake noise")
    execution_job.complete()

    repository.save(execution_job)
    restored = repository.get_by_service_order_id("os-1")

    assert restored.execution_id == execution_job.execution_id
    assert restored.status == ExecutionStatus.COMPLETED
    assert restored.steps[0].description == "Diagnose brake noise"


def test_mongo_repository_raises_clear_errors_when_missing() -> None:
    repository = MongoExecutionJobRepository(FakeMongoCollection())

    with pytest.raises(KeyError, match="Execution job not found"):
        repository.get("missing")


def test_in_memory_publisher_keeps_event_order() -> None:
    publisher = InMemoryEventPublisher()
    first = DomainEvent(event_type="FIRST", correlation_id="os-1", payload={})
    second = DomainEvent(event_type="SECOND", correlation_id="os-1", payload={})

    publisher.publish(first)
    publisher.publish(second)

    assert publisher.events == [first, second]
