COMPOSE_DEV = docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml
MIGRATE_SERVICES = auth-service course-service progress-service

.PHONY: run-dev down-dev build-dev logs-dev shell-service-dev test test-auth auth-test-db test-course course-test-db test-gateway env-init keys-init migrate seed-courses

# ============
# DEV COMMANDS
# ============
run-dev:
	$(COMPOSE_DEV) up -d $(ARGS)

down-dev:
	$(COMPOSE_DEV) down

build-dev:
	$(COMPOSE_DEV) build $(ARGS)

logs-dev:
	$(COMPOSE_DEV) logs $(SERVICE)

shell-service-dev:
	$(COMPOSE_DEV) exec -it $(SERVICE) sh -lc 'command -v bash >/dev/null 2>&1 && exec bash || exec sh'

# =======
# SCRIPTS
# =======
env-init:
	./scripts/init-env.sh

keys-init:
	./scripts/init-jwt-keys.sh

seed-courses:
	python3 scripts/seed_courses.py

migrate:
ifeq ($(SERVICE),)
	@for svc in $(MIGRATE_SERVICES); do \
		echo "Running migrations for $$svc..."; \
		$(COMPOSE_DEV) exec -T $$svc alembic -c alembic.ini upgrade head; \
	done
else
	$(COMPOSE_DEV) exec -T $(SERVICE) alembic -c alembic.ini upgrade head
endif

# =============
# TEST COMMANDS
# =============
test: test-auth test-course

test-gateway:
	$(COMPOSE_DEV) run --rm gateway-tests

test-auth: auth-test-db
	$(COMPOSE_DEV) exec -T auth-service pytest

auth-test-db:
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'auth_db_test';" | grep -q 1 || \
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -c "CREATE DATABASE auth_db_test;"

test-course: course-test-db
	$(COMPOSE_DEV) exec -T course-service pytest

course-test-db:
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'course_db_test';" | grep -q 1 || \
	$(COMPOSE_DEV) exec -T postgres psql -U postgres -c "CREATE DATABASE course_db_test;"
