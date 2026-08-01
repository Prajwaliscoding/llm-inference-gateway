test:
	uv run pytest --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --reload

lint:
	uv run ruff check .