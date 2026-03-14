from pydantic_settings import BaseSettings

from pathlib import Path


BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DATABASE_SYNC_URL: str = ""
    DATABASE_TEST_URL: str = ""
    SERVICE_NAME: str = "course-service"
    LOG_LEVEL: str = "INFO"
    SQL_DEBUG: bool = False
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    AUTH_JWT_PUBLIC_KEY: Path = BASE_DIR / "core" / "certs" / "jwt-public.pem"


settings = Settings()
