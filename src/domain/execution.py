"""Execution aggregate for diagnosis and repair progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from src.domain.events import DomainEvent


class ExecutionStatus(StrEnum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


TERMINAL_STATUSES = {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED}


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Execution step description is required")


@dataclass(slots=True)
class ExecutionJob:
    service_order_id: str
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus = ExecutionStatus.QUEUED
    steps: list[ExecutionStep] = field(default_factory=list)
    failure_reason: str | None = None

    @classmethod
    def enqueue(cls, service_order_id: str) -> tuple["ExecutionJob", DomainEvent]:
        if not service_order_id.strip():
            raise ValueError("Service order id is required")
        job = cls(service_order_id=service_order_id)
        return job, job._event("EXECUTION_QUEUED", {})

    def start(self) -> DomainEvent:
        if self.status != ExecutionStatus.QUEUED:
            raise ValueError("Only queued executions can start")
        self.status = ExecutionStatus.IN_PROGRESS
        return self._event("EXECUTION_STARTED", {})

    def add_step(self, description: str) -> None:
        if self.status != ExecutionStatus.IN_PROGRESS:
            raise ValueError("Steps can only be added while execution is in progress")
        self.steps.append(ExecutionStep(description=description))

    def complete(self) -> DomainEvent:
        if self.status != ExecutionStatus.IN_PROGRESS:
            raise ValueError("Only in-progress executions can complete")
        if not self.steps:
            raise ValueError("Execution must have at least one step before completion")
        self.status = ExecutionStatus.COMPLETED
        return self._event("EXECUTION_COMPLETED", {"step_count": len(self.steps)})

    def fail(self, reason: str) -> DomainEvent:
        if self.status in TERMINAL_STATUSES:
            raise ValueError("Terminal executions cannot fail again")
        if not reason.strip():
            raise ValueError("Failure reason is required")
        self.status = ExecutionStatus.FAILED
        self.failure_reason = reason
        return self._event("EXECUTION_FAILED", {"reason": reason})

    def to_document(self) -> dict[str, object]:
        return {
            "execution_id": self.execution_id,
            "service_order_id": self.service_order_id,
            "status": self.status.value,
            "steps": [
                {
                    "description": step.description,
                    "created_at": step.created_at.isoformat(),
                }
                for step in self.steps
            ],
            "failure_reason": self.failure_reason,
        }

    def _event(self, event_type: str, payload: dict[str, object]) -> DomainEvent:
        base_payload = {
            "execution_id": self.execution_id,
            "service_order_id": self.service_order_id,
        }
        base_payload.update(payload)
        return DomainEvent(
            event_type=event_type,
            correlation_id=self.service_order_id,
            payload=base_payload,
        )
