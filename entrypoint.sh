#!/bin/sh
set -e

# Wait for Postgres when configured (compose sets POSTGRES_HOST).
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  python - <<'EOF'
import os, socket, time
host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"Postgres at {host}:{port} not reachable")
EOF
fi

python manage.py migrate --noinput

exec "$@"
