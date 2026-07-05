"""Use cases for execution workflow."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports import EventPublisherPort, ExecutionJobRepositoryPort
from src.domain.execution import ExecutionJob


@dataclass(frozen=True, slots=True)
class EnqueueExecutionCommand:
    service_order_id: str


class EnqueueExecutionUseCase:
    def __init__(
        self, repository: ExecutionJobRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, command: EnqueueExecutionCommand) -> ExecutionJob:
        execution_job, event = ExecutionJob.enqueue(command.service_order_id)
        self._repository.save(execution_job)
        self._publisher.publish(event)
        return execution_job


class StartExecutionUseCase:
    def __init__(
        self, repository: ExecutionJobRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, execution_id: str) -> ExecutionJob:
        execution_job = self._repository.get(execution_id)
        event = execution_job.start()
        self._repository.save(execution_job)
        self._publisher.publish(event)
        return execution_job


class CompleteExecutionUseCase:
    def __init__(
        self, repository: ExecutionJobRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, execution_id: str, steps: list[str]) -> ExecutionJob:
        execution_job = self._repository.get(execution_id)
        for step in steps:
            execution_job.add_step(step)
        event = execution_job.complete()
        self._repository.save(execution_job)
        self._publisher.publish(event)
        return execution_job


class FailExecutionUseCase:
    def __init__(
        self, repository: ExecutionJobRepositoryPort, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, execution_id: str, reason: str) -> ExecutionJob:
        execution_job = self._repository.get(execution_id)
        event = execution_job.fail(reason)
        self._repository.save(execution_job)
        self._publisher.publish(event)
        return execution_job
