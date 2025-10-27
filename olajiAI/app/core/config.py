from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8010
    ENV: str = "dev"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    CORE_API_BASE: str = "http://localhost:8000"
    SERVICE_TOKEN: str = "change_me"
    JWT_AUDIENCE: str = "schoolops"
    JWT_ALG: str = "HS256"
    JWT_LEEWAY: int = 30
    REDIS_URL: str = "redis://localhost:6379/5"
    HTTP_CONNECT_TIMEOUT: float = 5
    HTTP_READ_TIMEOUT: float = 25
    RETRY_ATTEMPTS: int = 2
    SLOT_TTL_SECONDS: int = 1800
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings()
