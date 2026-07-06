from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.execution import ExecutionJob


class ExecutionJobRepositoryPort(Protocol):
    def save(self, execution_job: ExecutionJob) -> None:
        ...

    def get(self, execution_id: str) -> ExecutionJob:
        ...

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        ...


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        ...


class ProcessedEventRepositoryPort(Protocol):
    def is_processed(self, event_id: str) -> bool:
        ...

    def mark_processed(
        self, event_id: str, event_type: str, correlation_id: str
    ) -> None:
        ...
