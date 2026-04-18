# AGENTS.md — Online Course Platform

## Правила

- Отвечай на русском

## Структура репозитория

    microservices/auth/      — сервис авторизации (RSA JWT, RabbitMQ события)
    microservices/course/    — каталог курсов (секции, категории, курсы)
    microservices/progress/  — отслеживание прогресса пользователя
    microservices/assistant/ — AI-чат (Ollama), минимальные зависимости
    infra/api-gateway/       — шлюз KrakenD (Go шаблоны + flexible config)
    infra/nginx/             — конфиг nginx
    frontend/                — React 19 + Vite 8
    scripts/                 — init-env.sh, init-jwt-keys.sh, seed_courses.py

## Быстрый старт

    # 1. Создать .env файлы для всех сервисов
    make env-init

    # 2. Сгенерировать RSA JWT пару ключей (auth → course cross-service аутентификация)
    make keys-init          # пропускается если ключи есть; --force для пересоздания

    # 3. Запустить всё
    make run-dev

    # 4. Применить миграции для всех сервисов
    make migrate            # auth, course, progress
    # или для одного сервиса:  make migrate SERVICE=auth

    Порты: auth :8000, course :8001, progress :8002, assistant :8003,
           gateway :8080, frontend :5173, nginx :3000,
           RabbitMQ admin :15672, PostgreSQL :5432

## Команды

    make test                    — полный набор тестов
    make test-auth               — тесты auth-сервиса
    make test-course             — тесты course-сервиса
    make test-gateway            — тесты gateway
    make logs-dev SERVICE=<svc>  — логи контейнера
    make shell-service-dev SERVICE=<svc>  — shell в контейнер
    make down-dev / build-dev    — остановить / пересобрать
    make seed-courses            — загрузить демо-данные

## Тесты

- Тесты запускаются **внутри** контейнеров против общего PostgreSQL.
- Тестовые БД создаются автоматически при первом запуске: auth_db_test, course_db_test.
- Auth + course тесты используют session-scoped async engine + nested SAVEPOINT rollback (см. conftest.py).
- Auth тесты требуют JWT ключи в microservices/auth/app/certs/jwt-{private,public}.pem.
- Course тесты требуют публичный ключ в microservices/course/app/core/certs/jwt-public.pem.
- Запустить один тест: make test-auth, затем
  docker compose exec -T auth-service pytest -q -k "test_name"

## Миграции

    make migrate SERVICE=auth    — alembic -c alembic.ini upgrade head
    make migrate SERVICE=course
    make migrate SERVICE=progress

    Новая миграция: alembic -c alembic.ini revision --autogenerate -m "описание"
    (запускать внутри контейнера сервиса)

## JWT / аутентификация

- Auth-сервис подписывает JWT **закрытым RSA-ключом**: microservices/auth/app/certs/jwt-private.pem
- Course-сервис проверяет JWT **открытым RSA-ключом**: microservices/course/app/core/certs/jwt-public.pem
- Ключи генерируются скриптом scripts/init-jwt-keys.sh
- make keys-init генерирует ключи и копирует публичный ключ в course-сервис

## Фронтенд

    cd frontend && npm run dev    — dev-сервер :5173, прокси /api → gateway :8080
    cd frontend && npm run lint   — ESLint flat config
    cd frontend && npm run build  — продакшн билд

## Чего избегать

- .env.dev / .env.prod заигнорены в git. Всегда запускайте make env-init первым.
- make keys-init не пересоздаст существующие ключи (если не использовать --force).
- KrakenD конфиг использует Go шаблоны: krakend.tmpl + JSON settings + шаблоны.
- Нет pyproject.toml — зависимости в per-service requirements.txt.
- Progress-сервис не использует RabbitMQ (в отличие от auth/course).
- Assistant-сервис минимален: FastAPI + httpx + pydantic.
