import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["MOCK"] = "1"
os.environ["API_KEYS"] = ""
os.environ["RATE_LIMIT_PER_MINUTE"] = "5"
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from runtime import reset_rate_limits  # noqa: E402


@pytest.fixture
def client():
    reset_rate_limits()
    with TestClient(app) as c:
        yield c


def envelope(response):
    body = response.json()
    assert set(body) == {"success", "data", "error", "meta"}
    assert set(body["meta"]) == {"request_id", "timestamp", "duration_ms", "version"}
    return body


def test_health_is_open_and_wrapped(client):
    body = envelope(client.get("/healthz"))
    assert body["success"] is True
    assert body["data"]["mock"] is True
    assert body["error"] is None


def test_chat_returns_reply_and_session(client):
    body = envelope(client.post("/v1/chat", json={"message": "hello"}))
    data = body["data"]
    assert data["reply"]
    assert data["turn"] == 1
    assert data["usage"]["total_tokens"] > 0
    assert len(data["session_id"]) == 12


def test_session_is_remembered_across_turns(client):
    first = client.post("/v1/chat", json={"message": "one"}).json()["data"]
    second = client.post(
        "/v1/chat", json={"message": "two", "session_id": first["session_id"]}
    ).json()["data"]
    assert second["session_id"] == first["session_id"]
    assert second["turn"] == 2

    detail = envelope(client.get(f"/v1/sessions/{first['session_id']}"))["data"]
    assert detail["message_count"] == 4
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]


def test_validation_error_uses_the_envelope(client):
    response = client.post("/v1/chat", json={"message": ""})
    assert response.status_code == 422
    body = envelope(response)
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"][0]["field"] == "message"


def test_unknown_session_returns_404_envelope(client):
    response = client.get("/v1/sessions/does-not-exist")
    assert response.status_code == 404
    assert envelope(response)["error"]["code"] == "session_not_found"


def test_unknown_route_returns_404_envelope(client):
    response = client.get("/v1/nope")
    assert response.status_code == 404
    assert envelope(response)["error"]["code"] == "not_found"


def test_delete_session(client):
    session_id = client.post("/v1/chat", json={"message": "hi"}).json()["data"]["session_id"]
    assert client.delete(f"/v1/sessions/{session_id}").json()["data"]["deleted"] is True
    assert client.delete(f"/v1/sessions/{session_id}").status_code == 404


def test_rate_limit_trips_and_reports_retry_after(client):
    for _ in range(5):
        client.get("/v1/metrics")
    response = client.get("/v1/metrics")
    assert response.status_code == 429
    body = envelope(response)
    assert body["error"]["code"] == "rate_limited"
    assert "Retry-After" in response.headers


def test_request_id_is_echoed(client):
    response = client.get("/healthz", headers={"X-Request-ID": "trace-me-123"})
    assert response.headers["X-Request-ID"] == "trace-me-123"
    assert response.json()["meta"]["request_id"] == "trace-me-123"


def test_stream_emits_ndjson_events(client):
    with client.stream("POST", "/v1/chat/stream", json={"message": "stream please"}) as response:
        assert response.headers["content-type"].startswith("application/x-ndjson")
        types = [line for line in response.iter_lines() if line]
    assert '"type": "start"' in types[0]
    assert '"type": "end"' in types[-1]


def test_api_key_enforced_when_configured(client, monkeypatch):
    import runtime

    monkeypatch.setattr(runtime, "API_KEYS", {"secret-key"})
    assert client.get("/v1/metrics").status_code == 401
    assert client.get("/v1/metrics", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/metrics", headers={"X-API-Key": "secret-key"}).status_code == 200