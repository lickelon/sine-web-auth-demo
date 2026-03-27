default:
    @just --list

build:
    docker build -t sine-web .

run:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env

compose-run:
    docker compose up -d --build

compose-down:
    docker compose down
