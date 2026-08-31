#!/usr/bin/env bash
#
# Start the Rochondra dev stack and then the API, in one go.
#
# Services (Postgres, Redis, MinIO) are defined in docker-compose.yml and
# declare their own healthchecks, so `--wait` blocks until each one actually
# accepts connections. That matters: the API touches MinIO in its `lifespan`
# startup hook, so launching uvicorn as soon as the containers exist is a race.
#
# Any arguments are forwarded to uvicorn:
#     ./scripts/dev.sh --port 8080
#
# To stop the containers afterwards:
#     docker compose down        # keep data
#     docker compose down -v     # wipe data (schema is recreated on next boot)
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Starting services (postgres, redis, minio)..."
docker compose up -d --wait

echo
echo "API      http://127.0.0.1:8000        (docs at /docs)"
echo "MinIO    http://localhost:9001        (rochondra / devpassword123)"
echo "Ctrl-C to stop the API; containers keep running."
echo

# exec so Ctrl-C reaches uvicorn directly rather than this wrapper.
exec uv run uvicorn api.main:app --reload "$@"
