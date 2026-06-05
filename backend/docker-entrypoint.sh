#!/usr/bin/env sh
set -e

# Apply database migrations, then hand off to the container command (uvicorn).
echo "Running database migrations..."
alembic upgrade head

echo "Starting: $*"
exec "$@"
