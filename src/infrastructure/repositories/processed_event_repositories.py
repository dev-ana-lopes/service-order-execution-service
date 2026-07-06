from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol


class MongoProcessedEventsCollectionPort(Protocol):
    def find_one(self, filter: dict[str, Any]) -> dict[str, Any] | None:
        ...

    def replace_one(
        self,
        filter: dict[str, Any],
        replacement: dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        ...


class InMemoryProcessedEventRepository:
    def __init__(self) -> None:
        self.events: set[str] = set()

    def is_processed(self, event_id: str) -> bool:
        return event_id in self.events

    def mark_processed(
        self, event_id: str, event_type: str, correlation_id: str
    ) -> None:
        self.events.add(event_id)


class MongoProcessedEventRepository:
    def __init__(self, collection: MongoProcessedEventsCollectionPort) -> None:
        self._collection = collection

    def is_processed(self, event_id: str) -> bool:
        return self._collection.find_one({"event_id": event_id}) is not None

    def mark_processed(
        self, event_id: str, event_type: str, correlation_id: str
    ) -> None:
        self._collection.replace_one(
            {"event_id": event_id},
            {
                "event_id": event_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "processed_at": datetime.now(UTC).isoformat(),
            },
            upsert=True,
        )
