from __future__ import annotations

from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.messaging.rabbitmq_blocking_publisher import (
    RabbitMqBlockingEventPublisher,
)
from src.infrastructure.repositories.in_memory_execution_repository import (
    InMemoryExecutionJobRepository,
)
from src.infrastructure.repositories.mongo_execution_repository import (
    MongoExecutionJobRepository,
)


def build_execution_repository(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        from pymongo import MongoClient

        client = MongoClient(settings.MONGODB_URL)
        database = client.get_default_database()
        return MongoExecutionJobRepository(database["execution_jobs"])
    return InMemoryExecutionJobRepository()


def build_event_publisher(settings: Settings):
    if settings.APP_RUNTIME_MODE == "real":
        return RabbitMqBlockingEventPublisher(
            settings.RABBITMQ_URL,
            settings.RABBITMQ_EXCHANGE,
            settings.RABBITMQ_ROUTING_KEY,
            settings.RABBITMQ_QUEUE,
        )
    return InMemoryEventPublisher()
