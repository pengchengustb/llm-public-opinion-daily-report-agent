.PHONY: install test lint api dashboard daily evaluate validate compose-up compose-config

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

daily:
	python -m app run-daily --seed-sample

evaluate:
	python -m app evaluate-mock

validate:
	python -m app validate-demo

compose-up:
	docker compose up --build

compose-config:
	docker compose config
