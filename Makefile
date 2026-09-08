.PHONY: install run test lint demo

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --port 8001

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests

demo:
	python -m app.demo

