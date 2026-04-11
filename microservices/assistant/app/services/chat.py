import json
import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("app.services.chat")


async def warmup_ollama() -> None:
    url = f"{settings.OLLAMA_BASE_URL}/chat/completions"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "temperature": 0.0,
        "max_tokens": 4,
        "messages": [{"role": "user", "content": "Ответь одним словом: ок"}],
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
    }
    logger.info(
        "Starting Ollama warmup: model=%s timeout=%.1fs keep_alive=%s",
        settings.OLLAMA_MODEL,
        settings.OLLAMA_WARMUP_TIMEOUT_SECONDS,
        settings.OLLAMA_KEEP_ALIVE,
    )
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=settings.OLLAMA_WARMUP_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except Exception as exc:
        logger.exception(
            "Ollama warmup failed: type=%s details=%r",
            type(exc).__name__,
            exc,
        )
        return
    elapsed = time.perf_counter() - started_at
    logger.info("Ollama warmup finished successfully in %.2fs", elapsed)


def _fallback_recommendations(
    user_message: str,
    courses: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, str]]:
    query_tokens = {
        token.strip(".,!?;:()[]{}\"'").lower()
        for token in user_message.split()
        if len(token.strip()) >= 3
    }

    def score(course: dict[str, Any]) -> int:
        haystack = " ".join(
            [
                str(course.get("title") or ""),
                str(course.get("description") or ""),
                str(course.get("level") or ""),
            ]
        ).lower()
        return sum(1 for token in query_tokens if token and token in haystack)

    ranked = sorted(courses, key=score, reverse=True)
    selected = ranked[:limit]

    recommendations: list[dict[str, str]] = []
    for course in selected:
        course_id = str(course.get("id") or "").strip()
        title = str(course.get("title") or "").strip()
        if not course_id or not title:
            continue
        level = str(course.get("level") or "").strip()
        price = course.get("price")
        reason_parts = []
        if level:
            reason_parts.append(f"уровень: {level}")
        if price is not None:
            reason_parts.append(f"цена: {price}")
        reason_parts.append("подобран при временном fallback без LLM")
        recommendations.append(
            {
                "course_id": course_id,
                "title": title,
                "reason": ", ".join(reason_parts),
            }
        )
    return recommendations


def _build_courses_context(courses: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for course in courses[: settings.MAX_COURSES_IN_CONTEXT]:
        lines.append(
            json.dumps(
                {
                    "course_id": str(course.get("id")),
                    "title": course.get("title"),
                    "description": (course.get("description") or "")[:120],
                    "level": course.get("level"),
                    "price": course.get("price"),
                    "category_id": str(course.get("category_id") or ""),
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


async def fetch_published_courses(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    url = f"{settings.COURSE_SERVICE_URL}/courses/"
    params = {"skip": 0, "limit": settings.COURSE_FETCH_LIMIT}
    started_at = time.perf_counter()
    logger.info(
        "Fetching courses from course-service: url=%s params=%s",
        url,
        params,
    )
    response = await client.get(url, params=params)
    elapsed = time.perf_counter() - started_at
    logger.info(
        "Course-service response: status=%s elapsed=%.2fs",
        response.status_code,
        elapsed,
    )
    response.raise_for_status()

    data = response.json()
    if isinstance(data, dict) and isinstance(data.get("collection"), list):
        # Keep compatibility with collection envelope if upstream changes contract.
        data = data["collection"]

    if not isinstance(data, list):
        logger.warning("Unexpected courses payload type: %s", type(data).__name__)
        return []

    published_courses = [
        item for item in data if item.get("status") not in {"DRAFT", "ARCHIVED"}
    ]
    logger.info("Published courses fetched: total=%s", len(published_courses))
    return published_courses


async def generate_assistant_reply(
    *,
    user_message: str,
    history: list[dict[str, str]],
    courses: list[dict[str, Any]],
) -> dict[str, Any]:
    started_at = time.perf_counter()
    logger.info(
        "Generating assistant reply: user_message_len=%s history_len=%s courses_count=%s",
        len(user_message),
        len(history),
        len(courses),
    )

    system_prompt = (
        "You are an educational assistant for an online course platform. "
        "Answer in Russian. Recommend relevant courses only from COURSE_CATALOG. "
        "Do not invent course IDs or titles. Keep answers concise and useful. "
        "Return valid JSON with keys: answer (string), recommended_courses (array of max 3). "
        "Each recommended item must contain: course_id, title, reason."
    )

    catalog = _build_courses_context(courses)
    logger.info(
        "Prepared course catalog for LLM: chars=%s entries=%s",
        len(catalog),
        min(len(courses), settings.MAX_COURSES_IN_CONTEXT),
    )
    user_payload = f"COURSE_CATALOG:\n{catalog}\n\n" f"USER_QUESTION:\n{user_message}"

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-settings.MAX_HISTORY_MESSAGES :])
    messages.append({"role": "user", "content": user_payload})
    logger.info("Prepared %s messages for Ollama", len(messages))

    async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
        url = f"{settings.OLLAMA_BASE_URL}/chat/completions"
        logger.info(
            "Sending request to Ollama: url=%s model=%s timeout=%.1fs",
            url,
            settings.OLLAMA_MODEL,
            settings.OLLAMA_TIMEOUT_SECONDS,
        )
        try:
            ollama_started_at = time.perf_counter()
            response = await client.post(
                url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "temperature": 0.2,
                    "max_tokens": 140,
                    "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                    "messages": messages,
                },
            )
            ollama_elapsed = time.perf_counter() - ollama_started_at
            logger.info(
                "Ollama response received: status=%s elapsed=%.2fs",
                response.status_code,
                ollama_elapsed,
            )
            if response.status_code >= 400:
                logger.error(
                    "Ollama error response body(first 400 chars): %s",
                    response.text[:400],
                )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.exception(
                "Request to Ollama failed: type=%s details=%r",
                type(exc).__name__,
                exc,
            )
            fallback = _fallback_recommendations(user_message, courses, limit=3)
            return {
                "answer": (
                    "Сейчас генерация ответа от ИИ заняла слишком много времени. "
                    "Показываю подходящие курсы по быстрому fallback-поиску."
                ),
                "recommended_courses": fallback,
            }

    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    logger.info(
        "Received content from Ollama: content_len=%s preview(first 300 chars)=%s",
        len(content),
        content[:300],
    )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(
            "Ollama returned non-JSON content, fallback to plain answer. Preview=%s",
            content[:300],
        )
        parsed = {"answer": content, "recommended_courses": []}

    if not isinstance(parsed, dict):
        return {"answer": "Unable to parse model response.", "recommended_courses": []}

    answer = parsed.get("answer")
    recommended = parsed.get("recommended_courses")

    if not isinstance(answer, str) or not answer.strip():
        answer = "Unable to generate response."

    if not isinstance(recommended, list):
        recommended = []

    sanitized_recommended = []
    for item in recommended[:3]:
        if not isinstance(item, dict):
            logger.warning(
                "Skipped recommended item with invalid type: %s", type(item).__name__
            )
            continue
        course_id = item.get("course_id")
        title = item.get("title")
        reason = item.get("reason")
        if not all(
            isinstance(value, str) and value.strip()
            for value in [course_id, title, reason]
        ):
            logger.warning("Skipped invalid recommended item: %s", item)
            continue
        sanitized_recommended.append(
            {
                "course_id": course_id,
                "title": title,
                "reason": reason,
            }
        )

    total_elapsed = time.perf_counter() - started_at
    logger.info(
        "Assistant reply prepared: answer_len=%s recommendations=%s total_elapsed=%.2fs",
        len(answer),
        len(sanitized_recommended),
        total_elapsed,
    )
    return {"answer": answer, "recommended_courses": sanitized_recommended}
