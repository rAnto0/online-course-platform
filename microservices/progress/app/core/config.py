from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DATABASE_SYNC_URL: str = ""
    DATABASE_TEST_URL: str = ""
    SERVICE_NAME: str = "progress-service"
    LOG_LEVEL: str = "INFO"
    SQL_DEBUG: bool = False
    SECRET_KEY: str = ""
    AUTH_TOKEN_URL: str = "http://localhost:8000/auth/login"
    ENABLE_EVENTS: bool = False
    RABBITMQ_URL: str = ""
    RABBITMQ_EXCHANGE: str = "progress.events"


settings = Settings()
