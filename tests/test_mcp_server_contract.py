import mcp_server
from app.errors import AppError, ErrorCode
from app.reddit_service import ServiceResult


class FakeServiceSuccess:
    def fetch_thread_records(self, thread_id, max_comments=None, include_url=True):
        return ServiceResult(data=[{"id": thread_id, "type": "post"}], retries=1)

    def search_posts(self, subreddit, query, limit, sort="relevance"):
        return ServiceResult(data=[{"id": "post1", "title": "Example"}], retries=0)


class FakeServiceInvalidInput:
    def fetch_thread_records(self, thread_id, max_comments=None, include_url=True):
        raise AppError(ErrorCode.INVALID_INPUT, "invalid thread id")

    def search_posts(self, subreddit, query, limit, sort="relevance"):
        raise AppError(ErrorCode.INVALID_INPUT, "invalid search params")


def test_fetch_thread_comments_success_envelope(monkeypatch):
    monkeypatch.setattr(mcp_server, "get_shared_reddit_service", lambda: FakeServiceSuccess())

    response = mcp_server.fetch_thread_comments("abc123")

    assert response["success"] is True
    assert isinstance(response["request_id"], str)
    assert response["error"] is None
    assert isinstance(response["data"], list)
    assert response["meta"]["version"] == "v1"
    assert response["meta"]["retries"] == 1


def test_search_subreddit_success_envelope(monkeypatch):
    monkeypatch.setattr(mcp_server, "get_shared_reddit_service", lambda: FakeServiceSuccess())

    response = mcp_server.search_subreddit("python", "flask", 5, "relevance")

    assert response["success"] is True
    assert isinstance(response["request_id"], str)
    assert response["error"] is None
    assert isinstance(response["data"], list)
    assert response["meta"]["version"] == "v1"


def test_fetch_thread_comments_invalid_input_error(monkeypatch):
    monkeypatch.setattr(mcp_server, "get_shared_reddit_service", lambda: FakeServiceInvalidInput())

    response = mcp_server.fetch_thread_comments("bad")

    assert response["success"] is False
    assert response["data"] is None
    assert response["error"]["code"] == ErrorCode.INVALID_INPUT
    assert isinstance(response["request_id"], str)
