from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    predicthq_token: str
    api_base_url: str
    gemini_api_key: str
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    redis_url: str = "redis://localhost:6379/0"
    batch_size: int = 50
    max_workers: int = 4
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 1536
    
    class Config:
        env_file = ".env"


settings = Settings()