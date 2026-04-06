from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = "development"
    GEMINI_API_KEY: str
    MODEL_ID: str = "gemini-2.5-flash-lite"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()