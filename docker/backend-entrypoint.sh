#!/bin/sh
# Entrypoint shared by the web, worker, beat and seed containers.
# Only the web service sets RUN_MIGRATIONS=1 so migrations execute exactly once.
set -e

if [ "${DJANGO_ENV:-development}" = "production" ]; then
    case "${SECRET_KEY:-}" in
        ""|django-insecure*|*change-in-production*|*change-me*|*changeme*)
            echo "Refusing to start: DJANGO_ENV=production requires a real SECRET_KEY." >&2
            echo "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(50))'" >&2
            exit 1
            ;;
    esac
    if [ "${DB_PASSWORD:-}" = "didebaan_local_password" ]; then
        echo "Refusing to start: set a non-default DB_PASSWORD for production." >&2
        exit 1
    fi
fi

if [ "${WAIT_FOR_DB:-1}" = "1" ] && [ "$(printf '%s' "${USE_POSTGRES:-False}" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
deadline = time.time() + int(os.environ.get("DB_WAIT_SECONDS", "90"))

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"database {host}:{port} is reachable", flush=True)
            sys.exit(0)
    except OSError:
        time.sleep(2)

print(f"database {host}:{port} did not become reachable in time", file=sys.stderr, flush=True)
sys.exit(1)
PY
fi

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "Seeding fictional demo data..."
    python manage.py seed_demo
fi

exec "$@"
