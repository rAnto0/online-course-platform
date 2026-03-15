COMPOSE_DEV = docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml

.PHONY: run-dev down-dev build-dev test-auth auth-test-db

run-dev:
	$(COMPOSE_DEV) up -d $(ARGS)

down-dev:
	$(COMPOSE_DEV) down

build-dev:
	$(COMPOSE_DEV) build $(ARGS)

test-auth: auth-test-db
	$(COMPOSE_DEV) exec -T auth-service pytest

auth-test-db:
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'auth_db_test';" | grep -q 1 || \
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -c "CREATE DATABASE auth_db_test;"
