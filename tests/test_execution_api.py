import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from src.infrastructure.config.settings import Settings
from src.main import create_app


def test_app_has_execution_dependencies():
    app = create_app(_settings())

    assert hasattr(app.state, "execution_repository")
    assert hasattr(app.state, "event_publisher")


@pytest.mark.asyncio
async def test_execution_api_happy_path():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {_admin_token(settings)}"}

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        enqueue_response = await client.post(
            "/executions",
            json={"service_order_id": "os-1"},
            headers=headers,
        )
        execution_id = enqueue_response.json()["execution_id"]
        start_response = await client.post(
            f"/executions/{execution_id}/start",
            headers=headers,
        )
        complete_response = await client.post(
            f"/executions/{execution_id}/complete",
            json={"steps": ["Diagnose brake noise", "Replace brake pads"]},
            headers=headers,
        )
        by_service_order_response = await client.get(
            "/executions/by-service-order/os-1",
            headers=headers,
        )
        get_response = await client.get(
            f"/executions/{execution_id}",
            headers=headers,
        )

    assert enqueue_response.status_code == 201
    assert enqueue_response.json()["status"] == "QUEUED"
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "IN_PROGRESS"
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"
    assert by_service_order_response.status_code == 200
    assert by_service_order_response.json()["execution_id"] == execution_id
    assert get_response.status_code == 200
    assert len(get_response.json()["steps"]) == 2


@pytest.mark.asyncio
async def test_execution_api_returns_not_found():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/executions/missing",
            headers={"Authorization": f"Bearer {_admin_token(settings)}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execution_api_requires_valid_token():
    settings = _settings()
    app = create_app(settings)
    transport = ASGITransport(app=app)
    invalid_token = jwt.encode(
        {"role": "admin", "user_id": "admin-1"},
        "wrong-secret",
        algorithm="HS256",
    )

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        unauthorized = await client.get("/executions/missing")
        forbidden = await client.get(
            "/executions/missing",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

    assert unauthorized.status_code == 401
    assert forbidden.status_code == 403


def _settings() -> Settings:
    return Settings(
        APP_NAME="service-order-execution-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        JWT_SECRET="test-secret-value-with-32-characters",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
    )


def _admin_token(settings: Settings) -> str:
    return jwt.encode(
        {"role": "admin", "user_id": "admin-1", "iss": settings.JWT_ISSUER},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
