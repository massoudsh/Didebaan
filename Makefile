# Didebaan AML — Django best-practice run targets
# Usage: make run | make migrate | make test | make prod-run

PYTHON ?= python3
MANAGE = cd backend && $(PYTHON) manage.py
VENV = backend/venv
VENV_BIN = $(VENV)/bin

.PHONY: help venv install migrate run run-prod test shell createsuperuser collectstatic create-sample-rules

help:
	@echo "Didebaan AML — targets: venv, install, migrate, run, run-prod, test, shell, createsuperuser, collectstatic, create-sample-rules"

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

# Docker targets (Issue #37)
docker-build:
	docker build -t didebaan-aml .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

# Iran market setup
setup-iran:
	$(MANAGE) migrate
	$(MANAGE) createsuperuser --noinput || true
	$(MANAGE) create_sample_rules
	@echo "Iranian market setup complete."

# Lint (Issue #38)
lint:
	cd backend && flake8 . --max-line-length=120 --exclude=migrations,venv,.git,__pycache__
