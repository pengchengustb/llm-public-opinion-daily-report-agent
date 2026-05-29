.PHONY: install test lint run-api run-dashboard docker-up docker-down

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard:
	streamlit run dashboard/Home.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
