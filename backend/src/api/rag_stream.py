"""Server-sent events for streaming query progress."""
import json
import logging
from typing import AsyncIterator

from fastapi import HTTPException

from src.services.ollama_client_service import LLMUnavailableError

logger = logging.getLogger(__name__)


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_query_events(events: AsyncIterator[dict]) -> AsyncIterator[str]:
    """
    Relay pipeline events as SSE. The 200 status is already sent once streaming starts,
    so failures are reported as an "error" event and the stream ends without "done".
    """
    try:
        async for event in events:
            yield format_sse(event["event"], event["data"])
    except HTTPException as exc:
        yield format_sse("error", {"status_code": exc.status_code, "detail": exc.detail})
        return
    except LLMUnavailableError as exc:
        logger.error(f"LLM unavailable during streamed query: {exc}")
        yield format_sse("error", {"status_code": 503, "detail": "The language model is unavailable."})
        return
    except Exception:
        logger.exception("Streamed query failed")
        yield format_sse("error", {"status_code": 500, "detail": "Internal server error"})
        return

    yield format_sse("done", {})
