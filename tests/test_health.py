import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import Settings
from src.main import create_app


def test_create_app_in_real_mode_does_not_require_database_url():
    app = create_app(_real_settings())

    assert app.state.settings.DATABASE_URL is None
    assert hasattr(app.state, "readiness_checker")


@pytest.mark.asyncio
async def test_health_and_readiness_endpoints_return_operational_status_in_memory_mode():
    app = create_app(_memory_settings())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        health_response = await client.get("/health")
        readiness_response = await client.get("/health/ready")

    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "service": "service-order-execution-service",
        "version": "0.1.0",
        "environment": "test",
    }
    assert readiness_response.status_code == 200
    assert readiness_response.json()["checks"] == {"application": "ok"}


@pytest.mark.asyncio
async def test_readiness_in_real_mode_reports_dependency_success():
    app = create_app(_real_settings())
    app.state.readiness_checker._check_mongo = lambda: None
    app.state.readiness_checker._check_rabbitmq = lambda: None
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        readiness_response = await client.get("/health/ready")

    assert readiness_response.status_code == 200
    assert readiness_response.json()["checks"] == {
        "application": "ok",
        "mongo": "ok",
        "rabbitmq": "ok",
    }


@pytest.mark.asyncio
async def test_readiness_in_real_mode_reports_mongo_failure():
    app = create_app(_real_settings())

    def raise_mongo() -> None:
        raise RuntimeError("mongo unavailable")

    app.state.readiness_checker._check_mongo = raise_mongo
    app.state.readiness_checker._check_rabbitmq = lambda: None
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        readiness_response = await client.get("/health/ready")

    assert readiness_response.status_code == 503
    assert readiness_response.json()["checks"] == {
        "application": "ok",
        "mongo": "error",
        "rabbitmq": "ok",
    }


@pytest.mark.asyncio
async def test_readiness_in_real_mode_reports_rabbitmq_failure():
    app = create_app(_real_settings())
    app.state.readiness_checker._check_mongo = lambda: None

    def raise_rabbitmq() -> None:
        raise RuntimeError("rabbitmq unavailable")

    app.state.readiness_checker._check_rabbitmq = raise_rabbitmq
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        readiness_response = await client.get("/health/ready")

    assert readiness_response.status_code == 503
    assert readiness_response.json()["checks"] == {
        "application": "ok",
        "mongo": "ok",
        "rabbitmq": "error",
    }


def _memory_settings() -> Settings:
    return Settings(
        APP_NAME="service-order-execution-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        APP_RUNTIME_MODE="memory",
        JWT_SECRET="test-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
    )


def _real_settings() -> Settings:
    return Settings(
        APP_NAME="service-order-execution-service",
        APP_VERSION="0.1.0",
        ENVIRONMENT="test",
        APP_RUNTIME_MODE="real",
        MONGODB_URL="mongodb://mongo:27017/service_order",
        RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/%2F",
        JWT_SECRET="test-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
    )
