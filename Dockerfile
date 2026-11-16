# syntax=docker/dockerfile:1
# Didebaan — Django API image (used by the web, worker and beat services)
# Build context: repository root.  docker build -t didebaan-api .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    HOME=/app

WORKDIR /app

# Install dependencies first so source edits reuse the cached layer.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application source (the frontend is a separate image).
COPY backend/ ./

# Non-root runtime user. Logs, collected static and the beat schedule live in
# writable directories that Compose mounts as named volumes.
RUN addgroup --system aml \
    && adduser --system --ingroup aml --home /app --no-create-home aml \
    && mkdir -p /app/logs /app/staticfiles /app/beat \
    && chown -R aml:aml /app

COPY --chown=aml:aml docker/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
RUN chmod 0755 /usr/local/bin/backend-entrypoint.sh

USER aml

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=4)" || exit 1

ENTRYPOINT ["backend-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
