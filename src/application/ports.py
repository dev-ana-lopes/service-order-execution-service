from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.execution import ExecutionJob


class ExecutionJobRepositoryPort(Protocol):
    def save(self, execution_job: ExecutionJob) -> None:
        pass

    def get(self, execution_id: str) -> ExecutionJob:
        pass

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        pass


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        pass
