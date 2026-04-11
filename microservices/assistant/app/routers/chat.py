import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, status
import httpx

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import fetch_published_courses, generate_assistant_reply

logger = logging.getLogger("app.routers.chat")

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    request_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    logger.info(
        "[req=%s] Incoming chat request: message_len=%s history_len=%s",
        request_id,
        len(request.message),
        len(request.history),
    )
    try:
        courses_started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=20.0) as client:
            courses = await fetch_published_courses(client)
        logger.info(
            "[req=%s] Courses fetched: count=%s elapsed=%.2fs",
            request_id,
            len(courses),
            time.perf_counter() - courses_started_at,
        )

        history = [
            {"role": msg.role, "content": msg.content} for msg in request.history
        ]

        generation_started_at = time.perf_counter()
        result = await generate_assistant_reply(
            user_message=request.message,
            history=history,
            courses=courses,
        )
        logger.info(
            "[req=%s] Assistant response generated: answer_len=%s recommendations=%s elapsed=%.2fs",
            request_id,
            len(result.get("answer", "")),
            len(result.get("recommended_courses", [])),
            time.perf_counter() - generation_started_at,
        )
    except httpx.HTTPError as exc:
        logger.exception("[req=%s] Upstream HTTP error: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Assistant upstream request failed: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("[req=%s] Unexpected assistant error: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assistant internal error",
        ) from exc

    logger.info(
        "[req=%s] Chat request finished successfully in %.2fs",
        request_id,
        time.perf_counter() - started_at,
    )

    return ChatResponse(**result)
