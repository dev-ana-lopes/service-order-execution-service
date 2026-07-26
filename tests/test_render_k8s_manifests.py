from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = REPO_ROOT / "scripts" / "deploy" / "render_k8s_manifests.py"


def write_k8s_env(env_file: Path) -> None:
    env_file.write_text(
        "\n".join(
            [
                "APP_NAME=service-order-execution-service",
                "MONGODB_URL=mongodb://mongo:27017/service_order",
                "RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/%2F",
                "JWT_SECRET=jwt-secret-for-tests",
                "CUSTOMER_JWT_SECRET=customer-jwt-secret-for-tests",
                "APPROVAL_TOKEN_SECRET=approval-secret-for-tests",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_render(tmp_path: Path, *, image: str) -> subprocess.CompletedProcess[str]:
    env_file = tmp_path / "k8s.env"
    output_dir = tmp_path / "rendered-k8s"
    write_k8s_env(env_file)
    return subprocess.run(
        [
            sys.executable,
            str(RENDER_SCRIPT),
            "--env-file",
            str(env_file),
            "--output-dir",
            str(output_dir),
            "--image",
            image,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_render_k8s_manifests_injects_image_into_deployments(tmp_path: Path):
    image = "ghcr.io/example/-test"
    result = run_render(tmp_path, image=image)
    assert result.returncode == 0, result.stderr
    output_dir = tmp_path / "rendered-k8s"
    deployment = (output_dir / "deployment.yaml").read_text(encoding="utf-8")
    worker = (output_dir / "deployment-worker.yaml").read_text(encoding="utf-8")
    secret = (output_dir / "secret.rendered.yaml").read_text(encoding="utf-8")
    assert image in deployment
    assert image in worker
    assert "__API_IMAGE__" not in deployment
    assert "__API_IMAGE__" not in worker
    assert "DATABASE_URL" not in secret
    assert not (output_dir / "job-migrate.yaml").exists()


def test_render_k8s_manifests_rejects_empty_image(tmp_path: Path):
    result = run_render(tmp_path, image="   ")
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "non-empty container image reference" in combined_output


@pytest.mark.parametrize("image", ["${API_IMAGE}", "__API_IMAGE__", "<image>"])
def test_render_k8s_manifests_rejects_placeholder_like_image(tmp_path: Path, image: str):
    result = run_render(tmp_path, image=image)
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "rendered container image reference" in combined_output
