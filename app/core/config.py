from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = "development"
    GEMINI_API_KEY: str = "testing_only_key"
    MODEL_ID: str = "gemini-2.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()