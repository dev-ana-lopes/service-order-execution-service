from __future__ import annotations

from src.domain.execution import ExecutionJob


class InMemoryExecutionJobRepository:
    def __init__(self) -> None:
        self._items: dict[str, ExecutionJob] = {}

    def save(self, execution_job: ExecutionJob) -> None:
        self._items[execution_job.execution_id] = execution_job

    def get(self, execution_id: str) -> ExecutionJob:
        try:
            return self._items[execution_id]
        except KeyError as exc:
            raise KeyError(f"Execution job not found: {execution_id}") from exc

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        for execution_job in self._items.values():
            if execution_job.service_order_id == service_order_id:
                return execution_job
        raise KeyError(f"Execution job not found for service order: {service_order_id}")
