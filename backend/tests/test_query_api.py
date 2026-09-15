import json

import pytest
from fastapi.testclient import TestClient

import src.api.rag_routes as rag_routes
from src.api.deps import get_current_user
from src.main import app
from src.services.ollama_client_service import LLMUnavailableError

RESULT = {
    "query": "What drove revenue growth?",
    "results": [],
    "context": "",
    "llm_response": "Services.",
    "query_session": {"id": "qs-1", "conversation_id": "conv-1"},
}


@pytest.fixture
def client(user):
    app.dependency_overrides[get_current_user] = lambda: user
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_fake_pipeline(monkeypatch, error: Exception | None = None) -> list:
    calls = []

    async def answer_query_events(request, user):
        calls.append((request, user))
        yield {"event": "status", "data": {"message": "Retrieving relevant chunks"}}
        if error:
            raise error
        yield {"event": "result", "data": RESULT}

    monkeypatch.setattr(rag_routes.rag_service, "answer_query_events", answer_query_events)
    return calls


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))
    return events


def test_query_runs_pipeline_for_the_authenticated_user(client, monkeypatch, user):
    calls = use_fake_pipeline(monkeypatch)

    response = client.get("/api/rag/query", params={
        "query": "What drove revenue growth?",
        "with_llm_response": True,
        "document_ids": ["doc-1", "doc-2"],
        "conversation_id": "conv-1",
        "user_id": "someone-else",  # ignored: identity comes from the token
    })

    assert response.status_code == 200
    assert response.json() == RESULT
    request, called_with = calls[0]
    assert called_with is user
    assert request.document_ids == ["doc-1", "doc-2"]
    assert request.conversation_id == "conv-1"


def test_stream_emits_status_then_result_then_done(client, monkeypatch):
    use_fake_pipeline(monkeypatch)

    response = client.get("/api/rag/query", params={"query": "q", "stream": True})

    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert [name for name, _ in events] == ["status", "result", "done"]
    assert events[1][1] == RESULT


def test_llm_outage_returns_503(client, monkeypatch):
    use_fake_pipeline(monkeypatch, error=LLMUnavailableError("connection refused"))

    response = client.get("/api/rag/query", params={"query": "q", "with_llm_response": True})

    assert response.status_code == 503


def test_llm_outage_during_stream_emits_error_event_and_no_done(client, monkeypatch):
    use_fake_pipeline(monkeypatch, error=LLMUnavailableError("connection refused"))

    events = parse_sse(client.get("/api/rag/query", params={"query": "q", "stream": True}).text)

    assert [name for name, _ in events] == ["status", "error"]
    assert events[1][1]["status_code"] == 503
