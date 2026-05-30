.PHONY: install test lint api dashboard compose-up compose-config

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

api:
	python -m app api --reload

dashboard:
	streamlit run dashboard/app.py

compose-up:
	docker compose up --build

compose-config:
	docker compose config

