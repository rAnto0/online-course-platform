# Online Course Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Микросервисная платформа для онлайн-обучения: каталог и публикация курсов, прогресс студентов, централизованный API Gateway и AI-ассистент для рекомендаций.

> [!WARNING]
> Проект находится в активной разработке (work in progress). Архитектура и API могут меняться.

## Что уже реализовано

- микросервисная архитектура на FastAPI + PostgreSQL
- централизованный вход через KrakenD API Gateway
- JWT-аутентификация (RSA, access/refresh, JWKS)
- управление категориями, курсами, секциями и уроками
- роли пользователей (`student`, `author`, `admin`) и проверка прав
- трекинг зачислений и прогресса по курсам/урокам
- AI-ассистент (Ollama локально или Groq через конфиг)
- React 19 фронтенд (Vite 8, React Router 7)
- Docker Compose окружение для dev/prod
- автогенерация `.env.*`, генерация JWT-ключей, сидинг демо-данных
- интеграционные тесты gateway и unit/integration тесты сервисов

## Архитектура

```text
Frontend (React/Vite, :5173) / Nginx (:3000)
              |
              v
      API Gateway (KrakenD, :8080)
      /        |         |        \
     v         v         v         v
 Auth (:8000) Course (:8001) Progress (:8002) Assistant (:8003)
     |            |            |            |
     +------------+------------+------------+
                       |
                 PostgreSQL (:5432)

RabbitMQ (:5672, :15672) <-> auth/course events
Ollama (:11434) <-> assistant-service
```

## Технологический стек

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, Uvicorn
- Auth/безопасность: RSA JWT, JWKS, role-based access
- Messaging: RabbitMQ (`aio-pika`) для событий между сервисами
- Gateway: KrakenD (Go templates + flexible config)
- Frontend: React 19, Vite 8, React Router 7
- Infra: Docker Compose, Nginx, PostgreSQL 16, Ollama
- Тесты: pytest, pytest-asyncio, httpx

## Структура репозитория

```text
microservices/auth/      # авторизация, JWT, события
microservices/course/    # категории, курсы, секции, уроки
microservices/progress/  # зачисления и прогресс
microservices/assistant/ # AI-чат и рекомендации
infra/api-gateway/       # KrakenD конфиг и gateway-тесты
infra/nginx/             # nginx для dev/prod
frontend/                # React-приложение
scripts/                 # env/jwt init, сидинг
```

## Требования к окружению

- рекомендуемая ОС: Linux
- macOS обычно тоже работает без дополнительных изменений
- для Windows рекомендуется WSL2 (Ubuntu) + Docker Desktop

> Некоторые команды (`make ...`, `scripts/*.sh`) требуют POSIX-окружение и могут не работать в PowerShell/cmd без WSL.

## Быстрый старт (dev)

### 1) Подготовить окружение

```bash
make env-init
```

Команда создаст `.env.dev` и `.env.prod` во всех сервисах из `.env.example`, если файлов ещё нет.

### 2) Сгенерировать JWT RSA-ключи

```bash
make keys-init
```

Ключи для `auth` будут созданы в `microservices/auth/app/certs/`, публичный ключ будет скопирован в `course`.

### 3) Поднять проект

```bash
make run-dev
```

### 4) Применить миграции

```bash
make migrate
```

## Доступные порты(localhost)

- auth-service: `8000`
- course-service: `8001`
- progress-service: `8002`
- assistant-service: `8003`
- api-gateway: `8080`
- frontend (Vite): `5173`
- nginx: `3000`
- postgres: `5432`
- rabbitmq: `5672`
- rabbitmq admin: `15672`
- ollama: `11434`

## Основные команды

```bash
make run-dev                      # поднять dev-окружение
make down-dev                     # остановить dev-окружение
make build-dev                    # пересобрать контейнеры
make logs-dev SERVICE=<svc>       # логи сервиса
make shell-service-dev SERVICE=<svc>  # shell в контейнер сервиса

make migrate                      # миграции для auth/course/progress
make migrate SERVICE=auth-service # миграции конкретного сервиса

make test                         # test-auth + test-course
make test-auth                    # тесты auth
make test-course                  # тесты course
make test-gateway                 # тесты API gateway

make seed-courses                 # загрузить демо-курсы
```

## API через Gateway

Базовый URL: `http://localhost:8080`

- Auth: `/auth/*`
  - публичные: `POST /auth/login`, `POST /auth/register`, `GET /auth/health`
  - защищённые: `GET /auth/me`, `POST /auth/refresh`
- Course: `/categories*`, `/courses*` (чтение публичное, изменения под JWT)
- Progress: `/progress/*` (защищённые эндпоинты)
- Assistant: `POST /assistant/chat`, `GET /assistant/health`

## Аутентификация и права

- `auth-service` подписывает JWT приватным RSA-ключом
- `course-service` проверяет JWT публичным ключом
- KrakenD валидирует JWT через JWKS `auth/.well-known/jwks.json`
- Gateway прокидывает claims в заголовки:
  - `sub` -> `X-User-Id`
  - `role` -> `X-User-Role`

## События (RabbitMQ)

- `auth-service` и `course-service` используют RabbitMQ
- `progress-service` не использует RabbitMQ
- события включаются через env-настройки (`ENABLE_EVENTS`, `RABBITMQ_URL`)

## AI-ассистент

`assistant-service` поддерживает два режима:

- `LLM_PROVIDER=local` -> Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`)
- `LLM_PROVIDER=groq` -> Groq API (`GROQ_API_KEY`, `GROQ_MODEL`)

Ассистент получает опубликованные курсы из `course-service` и генерирует рекомендации.

## Фронтенд

- React 19 + Vite 8
- роуты: главная, карточка курса, просмотр урока, логин/регистрация, дашборд, профиль
- API-клиент с авто-refresh access токена
- запуск отдельно:

```bash
cd frontend
npm install
npm run dev
```

## Тестирование

- тесты запускаются внутри контейнеров
- автосоздаются test БД: `auth_db_test`, `course_db_test`
- для auth/course настроен session-scoped async engine + nested SAVEPOINT rollback

```bash
make test-auth
make test-course
make test-gateway
```

Запуск одного теста (пример):

```bash
docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml exec -T auth-service pytest -q -k "test_name"
```

## Миграции

```bash
make migrate
make migrate SERVICE=course-service
```

Новая миграция (внутри контейнера нужного сервиса):

```bash
alembic -c alembic.ini revision --autogenerate -m "описание"
alembic -c alembic.ini upgrade head
```

## Сидинг демо-данных

```bash
make seed-courses
```

Скрипт логинится под админом и создаёт категории/курсы/секции/уроки из `scripts/seed_courses.json`.

Полезные переменные:

- `SEED_BASE_URL` (по умолчанию `http://localhost:8080`)
- `SEED_USERNAME`, `SEED_PASSWORD`
- `SEED_COUNT`
- `SEED_PUBLISH`
- `SEED_DATA_FILE`

## Частые проблемы

- Нет `.env.*` файлов -> выполнить `make env-init`
- JWT-ключи не созданы -> выполнить `make keys-init`
- Course не валидирует токены -> проверить наличие `microservices/course/app/core/certs/jwt-public.pem`
- Assistant долго стартует -> это может быть warmup LLM на старте

## Roadmap (ближайшее)

- стабилизация контрактов API v1
- расширение покрытия тестами progress/assistant
- улучшение observability (метрики/трейсинг)
- усиление CI/CD и quality gates

## Лицензия

MIT
