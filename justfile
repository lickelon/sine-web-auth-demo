default:
    @just --list

build:
    docker build -t sine-web .

run:
    docker run --rm --name sine-web --env-file .env -p 8000:8000 -v ./data:/app/data sine-web

compose-run:
    docker compose up -d --build

compose-down:
    docker compose down
