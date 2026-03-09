from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .core.database import get_async_session
from .routers.auth import router as auth_router


app = FastAPI(title="Auth service")
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
