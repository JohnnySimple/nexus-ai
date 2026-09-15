import json

import httpx
import pytest

from src.services.ollama_client_service import LLMUnavailableError, OllamaClient


def client_with(handler) -> OllamaClient:
    return OllamaClient(base_url="http://ollama.test", timeout=5, transport=httpx.MockTransport(handler))


async def test_generate_returns_response_text_with_streaming_disabled():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "Services revenue grew 12%.", "done": True})

    answer = await client_with(handler).generate("mistral", "What drove growth?")

    assert answer == "Services revenue grew 12%."
    assert seen == {"path": "/api/generate", "body": {"model": "mistral", "prompt": "What drove growth?", "stream": False}}


async def test_generate_raises_on_error_status_instead_of_returning_placeholder_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'missing' not found"})

    with pytest.raises(LLMUnavailableError):
        await client_with(handler).generate("missing", "prompt")


async def test_generate_raises_when_server_is_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(LLMUnavailableError):
        await client_with(handler).generate("mistral", "prompt")


async def test_is_available_reflects_reachability():
    def up(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"version": "0.34.0"})

    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    assert await client_with(up).is_available() is True
    assert await client_with(down).is_available() is False
