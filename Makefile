COMPOSE_DEV = docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml
MIGRATE_SERVICES = auth-service course-service progress-service
PYTEST_ARGS ?= -q --disable-warnings -r fE

.PHONY: run-dev down-dev build-dev logs-dev shell-service-dev test test-auth auth-test-db test-course course-test-db test-progress progress-test-db test-gateway env-init keys-init migrate seed-courses

# =======
# HELPERS
# =======
define ensure_db
	@echo "Ensuring test database $(1)..."
	@$(COMPOSE_DEV) exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$(1)';" | grep -q 1 || $(COMPOSE_DEV) exec -T postgres psql -U postgres -c "CREATE DATABASE $(1);"
endef

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
test: test-auth test-course test-progress

test-gateway:
	@echo "Running gateway tests..."
	@$(COMPOSE_DEV) run --rm gateway-tests

test-auth: auth-test-db
	@echo "Running auth-service tests..."
	@$(COMPOSE_DEV) exec -T auth-service pytest $(PYTEST_ARGS)

auth-test-db:
	$(call ensure_db,auth_db_test)

test-course: course-test-db
	@echo "Running course-service tests..."
	@$(COMPOSE_DEV) exec -T course-service pytest $(PYTEST_ARGS)

course-test-db:
	$(call ensure_db,course_db_test)

test-progress: progress-test-db
	@echo "Running progress-service tests..."
	@$(COMPOSE_DEV) exec -T progress-service pytest $(PYTEST_ARGS)

progress-test-db:
	$(call ensure_db,progress_db_test)
