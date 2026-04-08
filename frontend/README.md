# Online Course Platform Frontend

Фронтенд для микросервисной платформы онлайн-курсов. Подключается к KrakenD API Gateway.

## Возможности

- каталог курсов с фильтрами и пагинацией
- авторизация, регистрация, профиль
- кабинет преподавателя/админа и студента
- управление курсами, секциями, уроками и категориями
- прогресс по урокам и курсам
- поддержка Markdown в описаниях и контенте уроков

## Локальный запуск (Vite)

```bash
npm install
npm run dev
```

По умолчанию фронтенд обращается к `http://localhost:8080`.

### Переменные окружения

- `VITE_API_BASE_URL` — прямой адрес API Gateway (например, `http://localhost:8080`)
- `VITE_API_PROXY_TARGET` — адрес для прокси в dev-режиме (если используется docker dev)

Пример:

```bash
VITE_API_BASE_URL=http://localhost:8080 npm run dev
```

## Запуск в Docker (dev)

В dev поднимаются и Vite, и nginx (для проверки прокси как в проде):

```bash
docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml up -d
```

- `http://localhost:5173` — прямой Vite
- `http://localhost:3000` — через nginx (как в проде)

## Сборка в Docker (prod)

В проде используется общий nginx из `infra/nginx`, который отдаёт статику и проксирует `/api`:

```bash
docker compose -f docker-compose.yaml up -d --build
```

Фронтенд будет доступен на `http://localhost:3000`.

## Примечания

- API Gateway должен быть доступен по адресу, заданному в переменных окружения.
- Markdown рендерится безопасно и используется для превью и полного отображения.
