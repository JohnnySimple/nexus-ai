"""
Ollama HTTP client with fallback mechanisms.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import requests

from src.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP client for Ollama API with graceful fallbacks."""

    def __init__(self, base_url: str = settings.OLLAMA_API_URL):
        self.base_url = base_url
        self.timeout = 30.0
        self._available = None

    async def _check_availability(self) -> bool:
        """Check if Ollama server is available."""
        if self._available is not None:
            return self._available

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                self._available = response.status_code == 200
                logger.info(f"Ollama availability: {self._available}")
                return self._available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
            return False

    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate completion from Ollama."""
        if not await self._check_availability():
            return self._mock_response(request)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # response = await client.post(
                #     f"{self.base_url}/api/generate",
                #     json=request,
                #     headers={"Content-Type": "application/json"}
                # )

                payload = {
                    "model": request["model"],
                    "prompt": request["prompt"],
                }

                response = requests.post(f"{self.base_url}/api/generate", json=payload)

                text = response.text
                
                if response.status_code == 200:
                    try:
                        return self._format_response(json.loads(text))  # Debug print
                    except json.JSONDecodeError:
                        try:
                            lines = text.strip().splitlines()
                            parsed = [json.loads(line) for line in lines if line.strip()]
                            return self._format_response(''.join([item['response'] for item in parsed if 'response' in item]))
                        except Exception:
                            return self._format_response(text)
                    
                else:
                    logger.warning(f"Ollama error {response.status_code}: {response.text}")
                    return self._mock_response(request)
                    
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return self._mock_response(request)

    async def generate_stream(self, request: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming completion from Ollama."""
        if not await self._check_availability():
            async for chunk in self._mock_stream(request):
                yield chunk
            return

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request["stream"] = True
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    chunk = json.loads(line)
                                    yield chunk
                                except json.JSONDecodeError:
                                    continue
                    else:
                        async for chunk in self._mock_stream(request):
                            yield chunk
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            async for chunk in self._mock_stream(request):
                yield chunk

    async def list_models(self) -> Dict[str, Any]:
        """List available models from Ollama."""
        if not await self._check_availability():
            return self._mock_models()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._mock_models()
                    
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return self._mock_models()

    def _format_response(self, response: str) -> Dict[str, Any]:
        return {
            "response": response
        }

    def _mock_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response when Ollama is unavailable."""
        prompt = request.get("prompt", "Hello")
        model = request.get("model", "llama2:7b")
        
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "response": f"Mock response for: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
            "done": True,
            "context": [],
            "total_duration": 1000000000,
            "load_duration": 500000000,
            "prompt_eval_count": len(prompt.split()),
            "eval_count": 20,
            "eval_duration": 500000000
        }

    async def _mock_stream(self, request: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate mock streaming response."""
        model = request.get("model", "llama2:7b")
        prompt = request.get("prompt", "Hello")
        
        # Simulate streaming by sending words individually
        words = f"Mock streaming response for: {prompt[:30]}".split()
        
        for i, word in enumerate(words):
            yield {
                "model": model,
                "created_at": "2024-01-01T00:00:00Z",
                "response": word + " ",
                "done": False
            }
            
        # Final chunk
        yield {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z", 
            "response": "",
            "done": True,
            "context": [],
            "total_duration": 1000000000,
            "prompt_eval_count": len(prompt.split()),
            "eval_count": len(words),
            "eval_duration": 500000000
        }

    def _mock_models(self) -> Dict[str, Any]:
        """Return mock model list when Ollama is unavailable."""
        return {
            "models": [
                {
                    "name": "llama2:7b",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 3825819519,
                    "digest": "mock-digest-1",
                    "details": {
                        "format": "gguf",
                        "family": "llama",
                        "families": ["llama"],
                        "parameter_size": "7B",
                        "quantization_level": "Q4_0"
                    }
                },
                {
                    "name": "mistral:7b",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 4109856768,
                    "digest": "mock-digest-2",
                    "details": {
                        "format": "gguf",
                        "family": "mistral",
                        "families": ["mistral"],
                        "parameter_size": "7B",
                        "quantization_level": "Q4_0"
                    }
                }
            ]
        }