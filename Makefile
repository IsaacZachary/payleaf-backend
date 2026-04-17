.PHONY: up down restart migrate makemigrations shell test lint format build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

shell:
	docker-compose exec web python manage.py shell

test:
	docker-compose exec web pytest

lint:
	docker-compose exec web ruff check .

format:
	docker-compose exec web black .

build:
	docker-compose build
