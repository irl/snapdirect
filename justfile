default:
  just --list

run *args:
  pybabel compile -d i18n
  poetry run uvicorn src.main:app --reload {{args}}

mm *args:
  poetry run alembic revision --autogenerate -m "{{args}}"

migrate:
  poetry run alembic upgrade head

downgrade *args:
  poetry run alembic downgrade {{args}}

black *args:
  poetry run black {{args}} src

ruff *args:
  poetry run ruff check {{args}} src

lint:
  poetry run ruff format src
  just ruff --fix

test:
  PYTHONPATH=. pytest tests

# docker
up:
  docker-compose up -d

kill *args:
  docker-compose kill {{args}}

build:
  docker-compose build

ps:
  docker-compose ps
