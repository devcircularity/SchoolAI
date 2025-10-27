from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "dev"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60
    REFRESH_EXPIRES_DAYS: int = 7

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()