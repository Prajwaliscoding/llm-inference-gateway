test:
	uv run pytest --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --reload

lint:
	uv run ruff check .

start-db:
	docker-compose up postgres redis -d

listall-key-redis:
	docker exec -it llm-inference-gateway-redis-1 redis-cli KEYS "cache:*"
# Then to see the value: docker exec -it llm-inference-gateway-redis-1 redis-cli GET cache:<cache-key>