
ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

COMPOSE_FILE := devops/docker/docker-compose.yaml

install:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

start:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) start

startAndBuild:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d --build

stop:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop

update:
	@git pull
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up --build -d
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) start

# ── Local development validation ─────────────────────────────────────────────

lint:
	~/.pyenv/versions/tutorai-env/bin/pre-commit run --all-files

test:
	~/.pyenv/versions/tutorai-env/bin/pytest -q --tb=short
	cd ui && npm run test:frontend

check: lint test

# ── Teacher classroom feature ────────────────────────────────────────────────

test-classrooms:
	~/.pyenv/versions/tutorai-env/bin/pytest tests/test_classrooms.py tests/test_attendance.py tests/test_classrooms_integration.py -v

test-ui-classrooms:
	cd ui && npx vitest run src/tests/classrooms.test.ts src/tests/attendanceTab.test.ts

e2e-classrooms:
	cd ui && npx cypress run --spec "cypress/e2e/classrooms.cy.ts"
