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
