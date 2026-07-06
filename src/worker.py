from __future__ import annotations

from src.application.event_handlers import ExecutionRequestEventHandler
from src.infrastructure.config.settings import get_settings
from src.infrastructure.runtime import (
    build_event_publisher,
    build_event_worker,
    build_execution_repository,
    build_processed_event_repository,
)


def main() -> int:
    settings = get_settings()
    handler = ExecutionRequestEventHandler(
        build_execution_repository(settings),
        build_event_publisher(settings),
        build_processed_event_repository(settings),
    )
    worker = build_event_worker(settings, handler.handle)
    try:
        worker.start()
    finally:
        worker.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
