from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any

class CustomBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class Config(CustomBaseSettings):
    RAG_VECTOR_STORE_PATH: str = "data/vector_store"
    RAG_EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_LLM_MODEL: str = "mistral"
    RAG_TOP_K: int = 5
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_USE_GPU: bool = True
    RAG_PERSISTENCE: bool = True
    RAG_FAISS_INDEX_FACTORY: str = "Flat"

    EMBEDDING_STORAGE_PATH: str = "data/embeddings"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: bool = True

    OLLAMA_API_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_MISTRAL: str = "mistral"

    CORS_ORIGINS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    SUPPORTED_FILE_TYPES: list[str] = ["txt", "pdf", "docx"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Config()

app_configs: dict[str, Any] = {
    "title": "RAG API Service",
    "version": "1.0.0",
}
