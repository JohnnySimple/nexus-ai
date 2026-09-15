"""Application settings, read from environment variables and backend/.env."""
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Embeddings, chunking and retrieval
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: bool = True
    CHUNK_MAX_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 50
    CHUNK_MIN_SENTENCE_LENGTH: int = 20
    WARM_MODELS_ON_STARTUP: bool = True

    # LLM
    OLLAMA_API_URL: str = "http://localhost:11434"
    DEFAULT_LLM_MODEL: str = "mistral"
    LLM_TIMEOUT_SECONDS: float = 120.0

    CORS_ORIGINS: list[str] = ["http://localhost:5001", "http://127.0.0.1:5001"]
    CORS_HEADERS: list[str] = ["*"]

    SUPPORTED_FILE_TYPES: list[str] = ["txt", "pdf"]

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    LOCAL_DOCUMENT_DIRECTORY_NAME: str = "nexus_ai_uploads"
    TEMP_UPLOAD_DIR: str = "data/temp_uploads"


settings = Config()

app_configs: dict[str, Any] = {
    "title": "RAG API Service",
    "version": "1.0.0",
}
