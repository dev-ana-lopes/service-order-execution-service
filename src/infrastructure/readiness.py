from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ReadinessResult:
    status_code: int
    payload: dict[str, object]


class ReadinessChecker:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check(self) -> ReadinessResult:
        checks: dict[str, str] = {"application": "ok"}

        if self._settings.APP_RUNTIME_MODE != "real":
            return ReadinessResult(
                status_code=200,
                payload={
                    "status": "ok",
                    "service": self._settings.APP_NAME,
                    "checks": checks,
                },
            )

        checks["mongo"] = self._dependency_status(self._check_mongo)
        checks["rabbitmq"] = self._dependency_status(self._check_rabbitmq)
        status_code = 200 if all(value == "ok" for value in checks.values()) else 503
        status = "ok" if status_code == 200 else "degraded"

        return ReadinessResult(
            status_code=status_code,
            payload={
                "status": status,
                "service": self._settings.APP_NAME,
                "checks": checks,
            },
        )

    def _dependency_status(self, check: Callable[[], None]) -> str:
        try:
            check()
        except Exception:
            return "error"
        return "ok"

    def _check_mongo(self) -> None:
        from pymongo import MongoClient

        timeout_ms = self._settings.HEALTHCHECK_TIMEOUT_SECONDS * 1000
        client = MongoClient(
            self._settings.MONGODB_URL,
            serverSelectionTimeoutMS=timeout_ms,
        )
        try:
            client.admin.command("ping")
        finally:
            client.close()

    def _check_rabbitmq(self) -> None:
        import pika

        timeout_seconds = self._settings.HEALTHCHECK_TIMEOUT_SECONDS
        parameters = pika.URLParameters(self._settings.RABBITMQ_URL)
        parameters.connection_attempts = 1
        parameters.blocked_connection_timeout = timeout_seconds
        parameters.socket_timeout = timeout_seconds
        parameters.stack_timeout = timeout_seconds

        connection = pika.BlockingConnection(parameters)
        try:
            connection.process_data_events(time_limit=0)
        finally:
            if connection.is_open:
                connection.close()


def build_readiness_checker(settings: Settings) -> ReadinessChecker:
    return ReadinessChecker(settings)
