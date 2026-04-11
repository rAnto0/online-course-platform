from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = 'assistant-service'
    LOG_LEVEL: str = 'INFO'
    COURSE_SERVICE_URL: str = 'http://course-service:8001'
    COURSE_FETCH_LIMIT: int = 1000
    OLLAMA_BASE_URL: str = 'http://ollama:11434/v1'
    OLLAMA_MODEL: str = 'qwen2.5:3b-instruct'
    OLLAMA_TIMEOUT_SECONDS: float = 240.0
    OLLAMA_WARMUP_ON_STARTUP: bool = True
    OLLAMA_WARMUP_TIMEOUT_SECONDS: float = 300.0
    OLLAMA_KEEP_ALIVE: str = '30m'
    MAX_HISTORY_MESSAGES: int = 10
    MAX_COURSES_IN_CONTEXT: int = 15


settings = Settings()
