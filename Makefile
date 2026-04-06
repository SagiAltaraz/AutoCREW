.PHONY: up down test test-e2e lint logs build

up:
	docker-compose up --build

down:
	docker-compose down

build:
	docker-compose build

test:
	pytest tests/unit/ -v

test-e2e:
	pytest tests/e2e/ -v

lint:
	ruff check agents/ backend/ data/

logs:
	docker-compose logs -f
