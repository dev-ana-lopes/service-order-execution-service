from __future__ import annotations

from typing import Any

from src.application.ports import (
    EventPublisherPort,
    ExecutionJobRepositoryPort,
    ProcessedEventRepositoryPort,
)
from src.application.use_cases import EnqueueExecutionCommand, EnqueueExecutionUseCase


class ExecutionRequestEventHandler:
    def __init__(
        self,
        execution_repository: ExecutionJobRepositoryPort,
        publisher: EventPublisherPort,
        processed_events: ProcessedEventRepositoryPort,
    ) -> None:
        self._execution_repository = execution_repository
        self._publisher = publisher
        self._processed_events = processed_events

    def handle(self, message: dict[str, Any]) -> str:
        event_id = str(message["event_id"])
        event_type = str(message["event_type"])
        correlation_id = str(message["correlation_id"])
        if self._processed_events.is_processed(event_id):
            return "skipped"
        if event_type != "EXECUTION_REQUESTED":
            return "ignored"

        payload = dict(message["payload"])
        EnqueueExecutionUseCase(
            self._execution_repository,
            self._publisher,
        ).execute(EnqueueExecutionCommand(str(payload["service_order_id"])))
        self._processed_events.mark_processed(event_id, event_type, correlation_id)
        return "processed"
