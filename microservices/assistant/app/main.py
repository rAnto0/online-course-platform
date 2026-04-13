import logging
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi import Request

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers.chat import router as chat_router
from app.services.chat import warmup_llm

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Running LLM warmup before accepting requests")
    await warmup_llm()
    logger.info("LLM warmup completed, service is ready")

    yield


app = FastAPI(title="Assistant service", lifespan=lifespan)
app.include_router(chat_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    logger.info(
        "HTTP request started: method=%s path=%s", request.method, request.url.path
    )
    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.perf_counter() - started_at
        logger.exception(
            "HTTP request failed: method=%s path=%s elapsed=%.2fs",
            request.method,
            request.url.path,
            elapsed,
        )
        raise
    elapsed = time.perf_counter() - started_at
    logger.info(
        "HTTP request finished: method=%s path=%s status=%s elapsed=%.2fs",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the Assistant service"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
