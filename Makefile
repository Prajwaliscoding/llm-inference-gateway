test:
	uv run pytest --cov=app --cov-report=term-missing

lint:
	uv run ruff check .

coverage_check:
	uv run pytest --cov=app tests/test_main.py -v

listall-key-redis:
	docker exec -it llm-inference-gateway-redis-1 redis-cli KEYS "cache:*"
# Then to see the value: docker exec -it llm-inference-gateway-redis-1 redis-cli GET cache:<cache-key>

# Primary local workflow: everything runs in Docker
# Requires .env to have POSTGRES_HOST=postgres and REDIS_HOST=redis
backend:
	docker compose up --build

frontend:
	cd frontend && npm run dev

dev:
	docker compose up --build -d && cd frontend && npm run dev