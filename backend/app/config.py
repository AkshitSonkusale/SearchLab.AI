import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = Field(default="SearchLab.AI", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    frontend_origin: str = Field(
        default="http://localhost:5173,https://searchlab-ai.vercel.app",
        validation_alias="FRONTEND_ORIGIN"
    )

    # Database
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", validation_alias="SUPABASE_SERVICE_KEY")
    supabase_storage_bucket: str = Field(default="documents", validation_alias="SUPABASE_STORAGE_BUCKET")

    # Groq LLM
    groq_api_key: str = Field(..., validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", validation_alias="GROQ_MODEL")

    # JWT Authentication
    jwt_secret: str = Field(default="supersecretrandomkeyforjwtencodinganddecoding32chars", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=480, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # RAG Settings
    relevance_threshold: float = Field(default=0.50, validation_alias="RELEVANCE_THRESHOLD")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", validation_alias="EMBEDDING_MODEL")
    top_k_chunks: int = Field(default=5, validation_alias="TOP_K_CHUNKS")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

