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

    response = mcp_server.search_subreddit("python", "flask", 5, "relevance")

    assert response["success"] is True
    assert isinstance(response["request_id"], str)
    assert response["error"] is None
    assert isinstance(response["data"], list)
    assert response["meta"]["version"] == "v1"


def test_fetch_thread_comments_invalid_input_error(monkeypatch):
    monkeypatch.setattr(mcp_server, "_call_service", fake_call_service_invalid_input)

    response = mcp_server.fetch_thread_comments("bad")

    assert response["success"] is False
    assert response["data"] is None
    assert response["error"]["code"] == ErrorCode.INVALID_INPUT
    assert isinstance(response["request_id"], str)
