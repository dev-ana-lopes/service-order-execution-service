# service-order-execution-service

FastAPI microservice responsible for execution queue, diagnosis/repair progress, completion, and execution failure events in the FIAP Phase 4 service-order system.

## Responsibility

This service owns execution jobs and execution status. It stores execution-oriented documents and does not read OS or Billing databases.

## Architecture

- `src/domain`: execution job entity, status transitions, steps, document representation, and domain events.
- `src/application`: use cases and ports for repositories and event publishers.
- `src/infrastructure`: settings, logging, in-memory and MongoDB repositories, observability, and messaging adapters.
- `src/presentation`: FastAPI routes, request/response schemas, and HTTP dependencies.

Business rules stay in `domain` and `application`; MongoDB, RabbitMQ, and HTTP details stay in infrastructure/presentation.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/executions` | Enqueue execution and publish `EXECUTION_QUEUED`. |
| `GET` | `/executions/{execution_id}` | Read an execution job. |
| `POST` | `/executions/{execution_id}/start` | Start execution and publish `EXECUTION_STARTED`. |
| `POST` | `/executions/{execution_id}/complete` | Add steps, complete execution, and publish `EXECUTION_COMPLETED`. |
| `POST` | `/executions/{execution_id}/fail` | Fail execution and publish `EXECUTION_FAILED`. |
| `GET` | `/events` | List published in-memory events for demo/test evidence. |
| `POST` | `/events/drain` | Drain published in-memory events for demo/test evidence. |
| `GET` | `/health` | Health check. |
| `GET` | `/health/live` | Liveness check. |
| `GET` | `/health/ready` | Readiness check. |
| `GET` | `/metrics` | Prometheus-style metrics endpoint. |

Swagger is available at `/docs` when the app is running.

## Events

Published by this service:

- `EXECUTION_QUEUED`
- `EXECUTION_STARTED`
- `EXECUTION_COMPLETED`
- `EXECUTION_FAILED`

The event envelope is JSON with `event_id`, `event_type`, `correlation_id`, `occurred_at`, and `payload`.

## Runtime Mode

`APP_RUNTIME_MODE` controls infrastructure adapters:

- `memory`: uses in-memory repository and publisher for local tests and fast demos.
- `real`: uses MongoDB repository and RabbitMQ publisher.

## NoSQL Ownership

Execution uses a MongoDB repository boundary for execution documents:

- `MongoExecutionJobRepository`
- `MONGODB_URL`

In `real` runtime mode, the app creates a PyMongo client from `MONGODB_URL` and stores execution jobs in the `execution_jobs` collection. For the low-cost demo, MongoDB should run as a lightweight container or in-cluster component instead of a managed DocumentDB service.

## Messaging

RabbitMQ integration is represented by thin infrastructure adapters:

- `RabbitMqEventPublisher`
- `RabbitMqEventConsumer`

Automated tests use fake channels only. They do not connect to production queues. In `real` runtime mode, the app publishes events to RabbitMQ through `RabbitMqBlockingEventPublisher`.

Environment variables:

- `RABBITMQ_URL`
- `RABBITMQ_EXCHANGE`
- `RABBITMQ_ROUTING_KEY`
- `RABBITMQ_QUEUE`

## Local Development

```bash
uv sync --dev
make lint
make test
make test-cov
make run-dev
```

## Validation Evidence

Latest local validation for Phase 7:

- `uv run --dev black src tests`
- `uv run --dev isort src tests`
- `uv run --dev black --check src tests`
- `uv run --dev isort --check-only src tests`
- `uv run --dev flake8 src tests`
- `uv run --dev pytest --cov=src --cov-report=term-missing --cov-report=xml -q`

Result: `27 passed`, `90%` coverage.

## CI/CD and Deploy

The GitHub Actions workflow validates lint, tests, coverage, SonarCloud, image build/push to GHCR, manifest rendering, and k3s deployment.

Kubernetes manifests are under `k8s/`. Manifests must be rendered with an explicit GHCR image before applying to the cluster.

## Cost Notes

The target demo uses EC2 with k3s, GHCR images, RabbitMQ inside k3s, MongoDB in-cluster, and shared low-cost infrastructure to stay within the AWS Academy budget.
