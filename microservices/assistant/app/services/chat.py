import json
import logging
import re
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("app.services.chat")


async def _warmup_local() -> None:
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


async def _warmup_groq() -> None:
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set, skipping Groq warmup")
        return
    url = f"{settings.GROQ_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": 0.0,
        "max_tokens": 4,
        "messages": [{"role": "user", "content": "Reply with one word: ok"}],
    }
    logger.info(
        "Starting Groq warmup: model=%s timeout=%.1fs",
        settings.GROQ_MODEL,
        settings.GROQ_WARMUP_TIMEOUT_SECONDS,
    )
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=settings.GROQ_WARMUP_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except Exception as exc:
        logger.exception(
            "Groq warmup failed: type=%s details=%r",
            type(exc).__name__,
            exc,
        )
        return
    elapsed = time.perf_counter() - started_at
    logger.info("Groq warmup finished successfully in %.2fs", elapsed)


async def warmup_llm() -> None:
    if settings.LLM_PROVIDER == "groq":
        if settings.GROQ_WARMUP_ON_STARTUP:
            await _warmup_groq()
        else:
            logger.info("Groq warmup on startup is disabled")
    else:
        if settings.OLLAMA_WARMUP_ON_STARTUP:
            await _warmup_local()
        else:
            logger.info("Ollama warmup on startup is disabled")


def _extract_json_from_text(text: str) -> str | None:
    """Извлекает JSON из текста. Ищет первый валидный JSON-объект."""
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return None


def _parse_llm_response(content: str) -> dict[str, Any]:
    """Парсит JSON-ответ от LLM, даже если вокруг есть лишний текст."""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    json_str = _extract_json_from_text(content)
    if json_str:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {"answer": content, "recommended_courses": []}


def _extract_query_tokens(user_message: str) -> set[str]:
    """Извлекаем ключевые слова из запроса (длина >= 3, без стоп-слов)."""
    # fmt: off
    stop_words = {
        "как", "что", "где", "когда", "кто", "почему", "зачем", "какой",
        "какая", "какое", "какие", "который", "которая", "которые",
        "хочу", "надо", "нужно", "мне", "бы", "ли", "же", "чтобы",
        "подскажите", "помогите", "расскажите", "посоветуйте",
        "для", "это", "его", "ее", "их", "мой", "твой", "свой",
        "the", "and", "for", "are", "but", "not", "you", "all",
        "can", "had", "her", "was", "one", "our", "out",
        "how", "what", "when", "where", "who", "why",
    }
    # fmt: on
    tokens: set[str] = set()
    for token in user_message.lower().split():
        cleaned = token.strip(".,!?;:()[]{}\"'")
        if len(cleaned) >= 3 and cleaned not in stop_words:
            tokens.add(cleaned)
    return tokens


def _score_course(course: dict[str, Any], query_tokens: set[str]) -> float:
    """Скоринг курса по релевантности запросу с весовыми коэффициентами."""
    if not query_tokens:
        return 0.0

    title = str(course.get("title") or "").lower()
    description = str(course.get("description") or "").lower()
    level = str(course.get("level") or "").lower()

    score = 0.0
    for token in query_tokens:
        # Точное совпадение по словам с весами
        if token in title:
            score += 3.0
        if token in description:
            score += 1.0
        if token in level:
            score += 2.0
        # Частичное совпадение (токен содержится в поле)
        title_words = set(title.split())
        desc_words = set(description.split())
        for word in title_words:
            if token in word or word in token:
                score += 1.5
        for word in desc_words:
            if token in word or word in token:
                score += 0.5

    return score


def _filter_relevant_courses(
    courses: list[dict[str, Any]],
    user_message: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Фильтрация курсов: скоринг по запросу, возврат топ-N релевантных."""
    query_tokens = _extract_query_tokens(user_message)
    if not query_tokens:
        # Если ключевых слов нет, возвращаем первые N курсов
        return courses[:limit]

    scored = [(course, _score_course(course, query_tokens)) for course in courses]
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    selected = ranked[:limit]

    logger.info(
        "Course filtering: tokens=%s scored=%s selected_top=%s max_score=%.1f",
        query_tokens,
        len(courses),
        len(selected),
        selected[0][1] if selected else 0,
    )

    return [course for course, _score in selected]


def _fallback_recommendations(
    user_message: str,
    courses: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, str]]:
    relevant = _filter_relevant_courses(courses, user_message, limit=limit * 3)
    recommendations: list[dict[str, str]] = []
    for course in relevant:
        if len(recommendations) >= limit:
            break
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
    for i, course in enumerate(courses, 1):
        title = course.get("title") or ""
        description = (course.get("description") or "")[:100]
        level = course.get("level") or ""
        price = course.get("price")
        parts = []
        if level:
            parts.append(f"уровень: {level}")
        if price is not None:
            parts.append(f"цена: {price}")
        meta = ", ".join(parts) if parts else ""
        lines.append(
            f"{i}. [{course.get('id')}] {title} | {meta}\n   {description}"
        )
    return "\n\n".join(lines)


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


async def _call_llm(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Вызов LLM через Groq или Ollama."""
    started_at = time.perf_counter()

    if settings.LLM_PROVIDER == "groq":
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set")
        url = f"{settings.GROQ_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        payload = {
            "model": settings.GROQ_MODEL,
            "temperature": 0.2,
            "max_tokens": 512,
            "messages": messages,
        }
        timeout = settings.GROQ_TIMEOUT_SECONDS
        logger.info(
            "Sending request to Groq: url=%s model=%s timeout=%.1fs",
            url,
            settings.GROQ_MODEL,
            timeout,
        )
    else:
        url = f"{settings.OLLAMA_BASE_URL}/chat/completions"
        headers = None
        payload = {
            "model": settings.OLLAMA_MODEL,
            "temperature": 0.2,
            "max_tokens": 140,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "messages": messages,
        }
        timeout = settings.OLLAMA_TIMEOUT_SECONDS
        logger.info(
            "Sending request to Ollama: url=%s model=%s timeout=%.1fs",
            url,
            settings.OLLAMA_MODEL,
            timeout,
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        llm_started_at = time.perf_counter()
        kwargs: dict[str, Any] = {"url": url, "json": payload}
        if headers:
            kwargs["headers"] = headers
        response = await client.post(**kwargs)
        llm_elapsed = time.perf_counter() - llm_started_at
        provider_name = "Groq" if settings.LLM_PROVIDER == "groq" else "Ollama"
        logger.info(
            "%s response received: status=%s elapsed=%.2fs",
            provider_name,
            response.status_code,
            llm_elapsed,
        )
        if response.status_code >= 400:
            logger.error(
                "%s error response body (first 400 chars): %s",
                provider_name,
                response.text[:400],
            )
        response.raise_for_status()
        return response.json()


async def generate_assistant_reply(
    *,
    user_message: str,
    history: list[dict[str, str]],
    courses: list[dict[str, Any]],
) -> dict[str, Any]:
    started_at = time.perf_counter()
    logger.info(
        "Generating assistant reply: user_message_len=%s history_len=%s courses_count=%s provider=%s",
        len(user_message),
        len(history),
        len(courses),
        settings.LLM_PROVIDER,
    )

    system_prompt = (
        "You are an educational assistant for an online course platform. "
        "Answer in Russian. "
        "You will receive a COURSE_CATALOG with numbered courses in format: "
        "'N. [course_id] Title | level: X, price: Y\\n   Description'. "
        "When the user asks about courses or learning, you MUST pick recommendations ONLY from COURSE_CATALOG. "
        "Use the exact course_id from the catalog (inside square brackets). "
        "Do not invent course IDs, titles, or descriptions. "
        "Keep answers concise and useful. "
        "Recommend courses ONLY when the user explicitly asks about courses, learning paths, "
        "or skill development. For greetings or general questions, return an empty "
        "recommended_courses array. "
        "Do NOT repeat your introduction if the user just says hello — respond naturally. "
        "Return valid JSON with keys: answer (string), recommended_courses (array of max 3). "
        "Each recommended item must contain: course_id, title, reason."
    )

    # Умная пред-фильтрация: скоринг - топ-N релевантных - LLM выбирает топ-3
    relevant_courses = _filter_relevant_courses(
        courses, user_message, limit=settings.MAX_COURSES_IN_CONTEXT
    )

    catalog = _build_courses_context(relevant_courses)
    logger.info(
        "Prepared course catalog for LLM: chars=%s entries=%s (filtered from %s total)",
        len(catalog),
        len(relevant_courses),
        len(courses),
    )
    user_payload = f"COURSE_CATALOG:\n{catalog}\n\n" f"USER_QUESTION:\n{user_message}"

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-settings.MAX_HISTORY_MESSAGES :])
    messages.append({"role": "user", "content": user_payload})
    provider_name = "Groq" if settings.LLM_PROVIDER == "groq" else "Ollama"
    logger.info("Prepared %s messages for %s", len(messages), provider_name)

    try:
        payload = await _call_llm(messages)
    except Exception as exc:
        logger.exception(
            "Request to LLM failed: type=%s details=%r",
            type(exc).__name__,
            exc,
        )
        fallback = _fallback_recommendations(user_message, courses, limit=3)
        return {
            "answer": (
                "Сейчас генерация ответа от ИИ недоступна. "
                "Показываю подходящие курсы по быстрому fallback-поиску."
            ),
            "recommended_courses": fallback,
        }

    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    logger.info(
        "Received content from LLM: content_len=%s preview(first 300 chars)=%s",
        len(content),
        content[:300],
    )

    parsed = _parse_llm_response(content)

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
