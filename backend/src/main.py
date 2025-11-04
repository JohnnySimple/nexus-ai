"""Main application entry point for the server."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
import logging
from dotenv import load_dotenv

from src.config import app_configs, settings

from src.api.rag_routes import router as rag_router
from src.api.auth.user_routes import router as auth_router
from src.api.document_routes import router as document_router
from src.api.query_routes import router as query_router
from src.api.dashboard_routes import router as dashboard_router
from src.schemas.user_schema import ResponseError

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
    allow_methods=("GET", "POST", "PUT", "PATH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(api_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseError(error=exc.detail).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom general exception handler."""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ResponseError(error="Internal server error").model_dump()
    )

@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
