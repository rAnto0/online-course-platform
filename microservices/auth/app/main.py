import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_async_session
from app.core.config import settings
from app.core.logging import setup_logging
from app.broker.rabbitmq import rabbitmq
from app.events.consumer import start_user_role_updated_consumer
from app.routers.auth import router as auth_router

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.ENABLE_EVENTS:
        logger.info("Events disabled")
        yield
        return
    if not settings.RABBITMQ_URL:
        logger.warning("RabbitMQ url is empty")
        yield
        return

    try:
        await rabbitmq.connect()
    except Exception:
        logger.exception("Failed to connect to RabbitMQ. Events publishing disabled.")
        yield
        return

    try:
        await start_user_role_updated_consumer()
    except Exception:
        logger.exception("Failed to start events consumer. Role updates disabled.")

    try:
        yield
    finally:
        await rabbitmq.close()


app = FastAPI(title="Auth service", lifespan=lifespan)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not origins and settings.DEBUG:
    origins = ["*"]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False if origins == ["*"] else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Auth service"}


@app.get("/health")
async def health(session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar() == 1
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "error"}
