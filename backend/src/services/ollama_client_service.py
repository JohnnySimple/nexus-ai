"""
Async Ollama HTTP client. Failures raise LLMUnavailableError instead of returning placeholder text.
"""

import logging
from functools import lru_cache
from typing import Any, Dict

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """The LLM backend could not produce a response."""


class OllamaClient:
    """HTTP client for the Ollama API."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = (base_url or settings.OLLAMA_API_URL).rstrip("/")
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self._transport = transport

    def _client(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=timeout, transport=self._transport)

    async def generate(self, model: str, prompt: str) -> str:
        """Generate a completion and return its text."""
        try:
            async with self._client(self.timeout) as client:
                response = await client.post(
                    "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response", "")
        except (httpx.HTTPError, ValueError) as e:
            raise LLMUnavailableError(f"Ollama generate with model '{model}' failed: {e}") from e

    async def list_models(self) -> Dict[str, Any]:
        """List models installed in Ollama."""
        try:
            async with self._client(10.0) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as e:
            raise LLMUnavailableError(f"Listing Ollama models failed: {e}") from e

    async def is_available(self) -> bool:
        """Cheap reachability check for health reporting."""
        try:
            async with self._client(2.0) as client:
                response = await client.get("/api/version")
                return response.status_code == 200
        except httpx.HTTPError as e:
            logger.warning(f"Ollama not available: {e}")
            return False


@lru_cache(maxsize=1)
def get_llm_client() -> OllamaClient:
    return OllamaClient()
