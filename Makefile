# Didebaan AML — Django best-practice run targets
# Usage: make run | make migrate | make test | make prod-run

PYTHON ?= python3
MANAGE = cd backend && $(PYTHON) manage.py
VENV = backend/venv
VENV_BIN = $(VENV)/bin

.PHONY: help venv install migrate run run-prod test shell createsuperuser collectstatic create-sample-rules check docker-build docker-up docker-down docker-stop docker-restart docker-ps docker-logs docker-seed docker-admin docker-migrate docker-test docker-reset

help:
	@echo "Didebaan AML — targets: venv, install, migrate, run, run-prod, test, shell, createsuperuser, collectstatic, create-sample-rules"
	@echo "Docker — targets: docker-build, docker-up, docker-down, docker-stop, docker-restart, docker-ps, docker-logs SERVICE=..., docker-seed, docker-admin, docker-migrate, docker-test, docker-reset"

venv:
	$(PYTHON) -m venv $(VENV)
	@echo "Activate with: source $(VENV_BIN)/activate"

install: venv
	$(VENV_BIN)/pip install -r backend/requirements.txt

migrate:
	$(MANAGE) migrate

run:
	$(MANAGE) runserver 0.0.0.0:8000

run-prod:
	export DJANGO_ENV=production && $(MANAGE) runserver 0.0.0.0:8000

test:
	$(MANAGE) test

shell:
	$(MANAGE) shell

createsuperuser:
	$(MANAGE) createsuperuser

collectstatic:
	$(MANAGE) collectstatic --noinput

create-sample-rules:
	$(MANAGE) create_sample_rules

check:
	$(MANAGE) check

# Docker targets — full stack from docker-compose.yml
COMPOSE ?= docker compose

docker-build:
	$(COMPOSE) build

docker-up:
	$(COMPOSE) up -d --build

docker-down:
	$(COMPOSE) down

docker-stop:
	$(COMPOSE) stop

docker-restart:
	$(COMPOSE) restart

docker-ps:
	$(COMPOSE) ps

docker-logs:
	$(COMPOSE) logs -f $(SERVICE)

docker-seed:
	$(COMPOSE) --profile demo run --rm seed

docker-admin:
	$(COMPOSE) exec backend python manage.py createsuperuser

docker-migrate:
	$(COMPOSE) exec backend python manage.py migrate --noinput

docker-test:
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 backend python manage.py test aml

docker-reset:
	$(COMPOSE) down -v

# Iran market setup
setup-iran:
	$(MANAGE) migrate
	$(MANAGE) createsuperuser --noinput || true
	$(MANAGE) create_sample_rules
	@echo "Iranian market setup complete."

# Lint (Issue #38)
lint:
	cd backend && flake8 . --max-line-length=120 --exclude=migrations,venv,.git,__pycache__
