# Deployment Runbook

Kubernetes is the primary deployment path. Docker Compose is available for local validation.

## Runtime

- API and worker run in the `service-order` namespace.
- Execution persistence is MongoDB through `MONGODB_URL`.
- RabbitMQ is configured through `RABBITMQ_URL` and the queue/exchange variables.
- MongoDB is the sole persistence store for this service.

## CI/CD

The workflow validates lint, tests, coverage and rendered manifests, then builds and publishes the image to GHCR. Deploy applies the namespace, ConfigMap, Secret, API Deployment, worker Deployment, Service, HPA and optional Ingress.

Required production secrets include `APP_ENV`, `EC2_SSH_KEY`, `EC2_HOST`, `EC2_USER` and `EC2_PORT`. `APP_ENV` must contain `MONGODB_URL`, RabbitMQ settings and application secrets.

## Local validation

```bash
uv sync --dev
make lint
make test
make compose-up
make compose-smoke
```
