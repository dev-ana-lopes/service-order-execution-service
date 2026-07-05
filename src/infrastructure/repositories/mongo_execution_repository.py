from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from src.domain.execution import ExecutionJob, ExecutionStatus, ExecutionStep


class MongoCollectionPort(Protocol):
    def replace_one(
        self,
        filter: dict[str, Any],
        replacement: dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        pass

    def find_one(self, filter: dict[str, Any]) -> dict[str, Any] | None:
        pass


class MongoExecutionJobRepository:
    def __init__(self, collection: MongoCollectionPort) -> None:
        self._collection = collection

    def save(self, execution_job: ExecutionJob) -> None:
        self._collection.replace_one(
            {"execution_id": execution_job.execution_id},
            execution_job.to_document(),
            upsert=True,
        )

    def get(self, execution_id: str) -> ExecutionJob:
        document = self._collection.find_one({"execution_id": execution_id})
        if document is None:
            raise KeyError(f"Execution job not found: {execution_id}")
        return self._from_document(document)

    def get_by_service_order_id(self, service_order_id: str) -> ExecutionJob:
        document = self._collection.find_one({"service_order_id": service_order_id})
        if document is None:
            raise KeyError(
                f"Execution job not found for service order: {service_order_id}"
            )
        return self._from_document(document)

    def _from_document(self, document: dict[str, Any]) -> ExecutionJob:
        return ExecutionJob(
            execution_id=str(document["execution_id"]),
            service_order_id=str(document["service_order_id"]),
            status=ExecutionStatus(str(document["status"])),
            steps=[
                ExecutionStep(
                    description=str(step["description"]),
                    created_at=datetime.fromisoformat(str(step["created_at"])),
                )
                for step in document.get("steps", [])
            ],
            failure_reason=document.get("failure_reason"),
        )
