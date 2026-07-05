"""Application ports for execution persistence and messaging."""

from __future__ import annotations

from typing import Protocol

from src.domain.events import DomainEvent
from src.domain.execution import ExecutionJob


class ExecutionJobRepositoryPort(Protocol):
    def save(self, execution_job: ExecutionJob) -> None:
        """Persist execution state."""

    def get(self, execution_id: str) -> ExecutionJob:
        """Return an execution job by id."""

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        """Return an execution job by service order id."""


class EventPublisherPort(Protocol):
    def publish(self, event: DomainEvent) -> None:
        """Publish an integration event."""
