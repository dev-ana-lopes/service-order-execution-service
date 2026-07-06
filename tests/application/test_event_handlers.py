from src.application.event_handlers import ExecutionRequestEventHandler
from src.domain.events import DomainEvent
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.repositories.in_memory_execution_repository import (
    InMemoryExecutionJobRepository,
)
from src.infrastructure.repositories.processed_event_repositories import (
    InMemoryProcessedEventRepository,
)


def test_execution_worker_handler_enqueues_execution_once() -> None:
    repository = InMemoryExecutionJobRepository()
    publisher = InMemoryEventPublisher()
    processed_events = InMemoryProcessedEventRepository()
    message = DomainEvent(
        event_id="event-1",
        event_type="EXECUTION_REQUESTED",
        correlation_id="os-1",
        payload={"service_order_id": "os-1"},
    ).to_message()
    handler = ExecutionRequestEventHandler(repository, publisher, processed_events)

    first_result = handler.handle(message)
    second_result = handler.handle(message)

    execution = repository.get_by_service_order_id("os-1")
    assert first_result == "processed"
    assert second_result == "skipped"
    assert execution.service_order_id == "os-1"
    assert publisher.events[0].event_type == "EXECUTION_QUEUED"
