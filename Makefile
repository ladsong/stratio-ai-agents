up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

migrate:
	docker compose run --rm migrate alembic upgrade head

migrate-down:
	docker compose run --rm migrate alembic downgrade -1

migrate-create:
	docker compose run --rm migrate alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose run --rm migrate python -m core.db.seed

# Testing
test:
	docker compose run --rm migrate pytest

test-unit:
	docker compose run --rm migrate pytest -m unit

test-integration:
	docker compose run --rm migrate pytest -m integration

test-cov:
	docker compose run --rm migrate pytest --cov=packages/core/src/core --cov-report=html --cov-report=term-missing

test-watch:
	docker compose run --rm migrate pytest -f

# Code Quality
lint:
	docker compose run --rm migrate ruff check packages/core/src apps/gateway/src apps/worker/src

format:
	docker compose run --rm migrate black packages/core/src apps/gateway/src apps/worker/src

format-check:
	docker compose run --rm migrate black --check packages/core/src apps/gateway/src apps/worker/src

# Combined checks
check: lint format-check test-unit

# Development
dev:
	docker compose up -d
	docker compose logs -f gateway worker

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

.PHONY: up down logs ps migrate migrate-down migrate-create seed test test-unit test-integration test-cov test-watch lint format format-check check dev clean
