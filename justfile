
set dotenv-load := true

CONTAINER_NAME := "otel-postgres-dev"

default: list

list:
    @just --list

setup:
    uv sync
    @echo "Environment ready. use 'just db-up' to start DB."

# --- Django ---

run:
    uv run python manage.py runserver

makemigrations:
    uv run python manage.py makemigrations

migrate:
    uv run python manage.py migrate

superuser:
    uv run python manage.py createsuperuser

lint:
    uv run ruff check --fix .
    uv run ruff format .

test:
    uv run pytest

# --- Postgres podman recipes ---
db-up:
    @if podman ps -a --format "{{.Names}}" | grep -q $(CONTAINER_NAME); then \
        echo "Starting DB container..."; \
        podman start $(CONTAINER_NAME); \
    else \
        echo "Building new DB container..."; \
        podman run -d \
            --name $(CONTAINER_NAME) \
            -e POSTGRES_DB=$(DB_NAME) \
            -e POSTGRES_USER=$(DB_USER) \
            -e POSTGRES_PASSWORD=$(DB_PASS) \
            -p 5432:5432 \
            -v postgres_data:/var/lib/postgresql/data \
            postgres:16-alpine; \
    fi
    @echo "DB ready listening on port 5432"

db-stop:
    podman stop $(CONTAINER_NAME)

db-nuke:
    podman rm -f $(CONTAINER_NAME)
    podman volume rm postgres_data || true

db-shell:
    podman exec -it $(CONTAINER_NAME) psql -U $(DB_USER) -d $(DB_NAME)
