from pathlib import Path

from scripts.deploy.prepare_env import prepare_env


def test_prepare_env_accepts_env_without_database_url(tmp_path: Path):
    env_file = tmp_path / ".env.prod"
    env_file.write_text(
        "\n".join(
            [
                "APP_NAME=service-order-execution-service",
                "APP_VERSION=1.0.0",
                "ENVIRONMENT=production",
                "LOG_LEVEL=info",
                "LOG_JSON=true",
                "APP_BASE_URL=https://api.example.com",
                "CORS_ALLOWED_ORIGINS=https://app.example.com",
                "TRUSTED_HOSTS=api.example.com",
                "JWT_ALGORITHM=HS256",
                "MONGODB_URL=mongodb://mongo:27017/service_order",
                "RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/%2F",
                "HEALTHCHECK_TIMEOUT_SECONDS=5",
                "APPROVAL_TOKEN_TTL_MINUTES=60",
                "JWT_EXPIRATION_MINUTES=60",
                "JWT_SECRET=test-secret",
                "CUSTOMER_JWT_SECRET=customer-secret",
                "APPROVAL_TOKEN_SECRET=approval-secret",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    prepare_env(env_file)

    contents = env_file.read_text(encoding="utf-8")
    assert "DATABASE_URL" not in contents
    assert 'CORS_ALLOWED_ORIGINS=["https://app.example.com"]' in contents
    assert 'TRUSTED_HOSTS=["api.example.com"]' in contents
