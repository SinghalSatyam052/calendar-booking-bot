from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    google_credentials: str = Field(..., env="GOOGLE_CREDENTIALS")
    calendar_id: str = Field(..., env="CALENDAR_ID")
    time_zone: str = Field("Asia/Kolkata", env="TIME_ZONE")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]