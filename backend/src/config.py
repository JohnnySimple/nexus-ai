from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

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

    OLLAMA_API_URL: str = os.getenv("LLM_URL")
    OLLAMA_MODEL_MISTRAL: str = "mistral"

    CORS_ORIGINS: list[str] = ["http://localhost:5001", "http://127.0.0.1:5001"]
    CORS_HEADERS: list[str] = ["*"]

    SUPPORTED_FILE_TYPES: list[str] = ["txt", "pdf", "docx"]

    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    USE_DB: bool = True

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    LOCAL_DOCUMENT_DIRECTORY_NAME: str = "nexus_ai_uploads"
    TEMP_UPLOAD_DIR: str = "data/temp_uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Config()

app_configs: dict[str, Any] = {
    "title": "RAG API Service",
    "version": "1.0.0",
}
