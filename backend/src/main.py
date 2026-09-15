"""Main application entry point for the server."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.api.auth.user_routes import router as auth_router
from src.api.dashboard_routes import router as dashboard_router
from src.api.document_routes import router as document_router
from src.api.query_routes import router as query_router
from src.api.rag_routes import router as rag_router
from src.config import app_configs, settings
from src.schemas.user_schema import ResponseError
from src.services.embeddings import get_embedding_service
from src.services.ollama_client_service import LLMUnavailableError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _load_models() -> None:
    get_embedding_service().reranker


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting server...")
    if settings.WARM_MODELS_ON_STARTUP:
        # Load models before accepting traffic so the first query doesn't pay for it.
        await asyncio.to_thread(_load_models)
        logger.info("Embedding and reranking models loaded")

    yield

api_router = APIRouter(prefix="/api")
api_router.include_router(rag_router, prefix="/rag", tags=["RAG"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(document_router, prefix="/documents", tags=["Documents"])
api_router.include_router(query_router, prefix="/query", tags=["Query"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

app = FastAPI(**app_configs, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(api_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseError(error=str(exc.detail)).model_dump(),
        headers=exc.headers,
    )

@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
    """The LLM is down or misconfigured: report it instead of answering with placeholder text."""
    logger.error(f"LLM unavailable on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=503,
        content=ResponseError(error="The language model is unavailable. Check that Ollama is running.").model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom general exception handler."""
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content=ResponseError(error="Internal server error").model_dump()
    )

@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
