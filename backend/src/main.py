"""Main application entry point for the server."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
import logging
from dotenv import load_dotenv

from src.config import app_configs, settings

from src.api.rag_routes import router as rag_router

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting server...")
    
    yield

app = FastAPI(**app_configs, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(rag_router, prefix="/rag", tags=["RAG"])


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
