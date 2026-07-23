# Didebaan AML — Dockerfile
# Issue #37: Containerized deployment for app, DB, Redis
# Usage:  docker build -t didebaan-aml .
#         docker-compose up

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY backend/ .

# Create non-root user
RUN addgroup --system aml && adduser --system --ingroup aml aml
RUN chown -R aml:aml /app
USER aml

# Create log directory
RUN mkdir -p /app/logs

EXPOSE 8000

# Run migrations then start gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && \
     python manage.py collectstatic --noinput && \
     gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"]
