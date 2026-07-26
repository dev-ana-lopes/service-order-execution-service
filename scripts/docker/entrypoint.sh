#!/usr/bin/env sh
set -eu

app_runtime_mode="${APP_RUNTIME_MODE:-memory}"

if [ "$app_runtime_mode" = "real" ]; then
  echo "[entrypoint] APP_RUNTIME_MODE=real; MongoDB and RabbitMQ are expected."
else
  echo "[entrypoint] APP_RUNTIME_MODE=${app_runtime_mode}; using in-memory adapters."
fi

echo "[entrypoint] Starting application: $*"
exec "$@"
