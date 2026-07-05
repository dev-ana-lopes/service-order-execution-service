import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import Settings
from src.main import create_app


def test_app_has_execution_dependencies():
    app = create_app(_settings())

    assert hasattr(app.state, "execution_repository")
    assert hasattr(app.state, "event_publisher")


@pytest.mark.asyncio
async def test_execution_api_happy_path():
    app = create_app(_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        enqueue_response = await client.post(
            "/executions", json={"service_order_id": "os-1"}
        )
        execution_id = enqueue_response.json()["execution_id"]
        start_response = await client.post(f"/executions/{execution_id}/start")
        complete_response = await client.post(
            f"/executions/{execution_id}/complete",
            json={"steps": ["Diagnose brake noise", "Replace brake pads"]},
        )
        get_response = await client.get(f"/executions/{execution_id}")

    assert enqueue_response.status_code == 201
    assert enqueue_response.json()["status"] == "QUEUED"
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "IN_PROGRESS"
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"
    assert get_response.status_code == 200
    assert len(get_response.json()["steps"]) == 2


@pytest.mark.asyncio
async def test_execution_api_returns_not_found():
    app = create_app(_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/executions/missing")

    assert response.status_code == 404


def _settings() -> Settings:
    return Settings(
        APP_NAME="service-order-execution-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="test-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
    )
