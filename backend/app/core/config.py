from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    predicthq_token: str = Field(alias="PREDICTHQ_TOKEN")
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    redis_url: str = "redis://localhost:6379/0"
    batch_size: int = 50
    max_workers: int = 4
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    
    class Config:
        env_file = ".env"


settings = Settings()