from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_entrypoint_no_longer_requires_database_url() -> None:
    entrypoint = (REPO_ROOT / "scripts" / "docker" / "entrypoint.sh").read_text(
        encoding="utf-8"
    )

    assert "DATABASE_URL is required" not in entrypoint
    assert "alembic" not in entrypoint


def test_local_compose_no_longer_references_postgres() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "postgres:" not in compose
    assert "DATABASE_URL:" not in compose


def test_prod_compose_uses_real_runtime_without_database_url() -> None:
    compose = (REPO_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")

    assert "APP_RUNTIME_MODE: ${APP_RUNTIME_MODE:-real}" in compose
    assert "DATABASE_URL:" not in compose
