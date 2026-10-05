import mcp_server
from app.errors import AppError, ErrorCode


def fake_call_service_success(path, params):
    if path == "/api/thread":
        return [{"id": params["thread_id"], "type": "post"}], 1
    return [{"id": "post1", "title": "Example"}], 0


def fake_call_service_invalid_input(path, params):
    raise AppError(ErrorCode.INVALID_INPUT, "invalid request")


def test_fetch_thread_comments_success_envelope(monkeypatch):
    monkeypatch.setattr(mcp_server, "_call_service", fake_call_service_success)

    response = mcp_server.fetch_thread_comments("abc123")

    assert response["success"] is True
    assert isinstance(response["request_id"], str)
    assert response["error"] is None
    assert isinstance(response["data"], list)
    assert response["meta"]["version"] == "v1"
    assert response["meta"]["retries"] == 1


def test_search_subreddit_success_envelope(monkeypatch):
    monkeypatch.setattr(mcp_server, "_call_service", fake_call_service_success)

    response = mcp_server.search_subreddit(
        query="flask",
        subreddit="python",
        limit=5,
        sort="relevance",
    )

    assert response["success"] is True
    assert isinstance(response["request_id"], str)
    assert response["error"] is None
    assert isinstance(response["data"], list)
    assert response["meta"]["version"] == "v1"


def test_search_subreddit_defaults_to_all(monkeypatch):
    calls = {}

    def capture_call(path, params):
        calls["path"] = path
        calls["params"] = params
        return [{"id": "post1", "title": "Example"}], 0

    monkeypatch.setattr(mcp_server, "_call_service", capture_call)

    response = mcp_server.search_subreddit(query="flask")

    assert response["success"] is True
    assert calls["path"] == "/api/search_posts"
    assert calls["params"]["subreddit"] == "all"


def test_fetch_thread_comments_invalid_input_error(monkeypatch):
    monkeypatch.setattr(mcp_server, "_call_service", fake_call_service_invalid_input)

    response = mcp_server.fetch_thread_comments("bad")

    assert response["success"] is False
    assert response["data"] is None
    assert response["error"]["code"] == ErrorCode.INVALID_INPUT
    assert isinstance(response["request_id"], str)


class FakeHttpResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_thread_comments_passes_not_found_through(monkeypatch):
    payload = {"success": False, "error": {"code": ErrorCode.NOT_FOUND, "message": "Reddit resource was not found"}}
    monkeypatch.setattr(mcp_server.requests, "get", lambda *a, **k: FakeHttpResponse(404, payload))

    response = mcp_server.fetch_thread_comments("abc123")

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.NOT_FOUND


def test_status_error_maps_404_and_403_without_body():
    assert mcp_server._status_error(404).code == ErrorCode.NOT_FOUND
    assert mcp_server._status_error(403).code == ErrorCode.FORBIDDEN
