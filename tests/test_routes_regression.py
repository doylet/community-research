import io

import pytest
from flask import Flask

import app.routes as routes
from app.errors import AppError, ErrorCode
from app.reddit_service import ServiceResult


class FakeService:
    def fetch_thread_records(self, thread_id, max_comments=None, include_url=False):
        return ServiceResult(
            data=[
                {
                    "type": "post",
                    "author": "poster",
                    "text": "title",
                    "score": 1,
                    "id": "abc123",
                    "parent_id": None,
                    "created_utc": 1,
                },
                {
                    "type": "comment",
                    "author": "commenter",
                    "text": "body",
                    "score": 2,
                    "id": "c1",
                    "parent_id": "t3_abc123",
                    "created_utc": 2,
                },
            ],
            retries=0,
        )


def test_search_route_preserves_csv_columns(monkeypatch):
    monkeypatch.setattr(routes, "get_shared_reddit_service", lambda: FakeService())

    app = Flask(__name__)
    app.register_blueprint(routes.main)

    with app.test_client() as client:
        response = client.get("/search?id=abc123")

    assert response.status_code == 200
    csv_body = response.data.decode("utf-8")
    first_line = io.StringIO(csv_body).readline().strip()
    assert first_line == "type,author,text,score,id,parent_id,created_utc"


class RaisingService:
    def __init__(self, exc):
        self._exc = exc

    def fetch_thread_records(self, *args, **kwargs):
        raise self._exc

    def search_posts(self, *args, **kwargs):
        raise self._exc


def client_with_service(monkeypatch, service):
    monkeypatch.setattr(routes, "get_shared_reddit_service", lambda: service)
    app = Flask(__name__)
    app.register_blueprint(routes.main)
    return app.test_client()


def test_search_route_rejects_malformed_thread_id(monkeypatch):
    from app.reddit_service import RedditService
    from tests.test_reddit_service import FakeClientSuccess, build_config

    service = RedditService(config=build_config(), reddit_client_factory=lambda cfg: FakeClientSuccess())
    with client_with_service(monkeypatch, service) as client:
        response = client.get("/search?id=bad!")

    assert response.status_code == 400


def test_search_route_not_found_returns_404(monkeypatch):
    with client_with_service(monkeypatch, RaisingService(AppError(ErrorCode.NOT_FOUND, "missing"))) as client:
        response = client.get("/search?id=abc123")

    assert response.status_code == 404
    assert "not found" in response.data.decode().lower()


def test_search_route_hides_unexpected_exception_text(monkeypatch):
    with client_with_service(monkeypatch, RaisingService(RuntimeError("internal-detail-xyz"))) as client:
        response = client.get("/search?id=abc123")

    assert response.status_code == 500
    assert "internal-detail-xyz" not in response.data.decode()


@pytest.mark.parametrize("subreddit_param", [None, ""])
def test_api_search_posts_defaults_missing_subreddit_to_all(monkeypatch, subreddit_param):
    class RecordingSearchService:
        def __init__(self):
            self.search_args = None

        def search_posts(self, **kwargs):
            self.search_args = kwargs
            return ServiceResult(data=[], retries=0)

    service = RecordingSearchService()
    query = "/api/search_posts?query=agentic"
    if subreddit_param is not None:
        query += f"&subreddit={subreddit_param}"

    with client_with_service(monkeypatch, service) as client:
        response = client.get(query)

    assert response.status_code == 200
    assert service.search_args["subreddit"] == "all"


@pytest.mark.parametrize(
    ("code", "status"),
    [(ErrorCode.NOT_FOUND, 404), (ErrorCode.FORBIDDEN, 403)],
)
@pytest.mark.parametrize(
    "path",
    ["/api/thread?thread_id=abc123", "/api/search_posts?subreddit=python&query=x"],
)
def test_api_routes_return_new_error_codes(monkeypatch, code, status, path):
    with client_with_service(monkeypatch, RaisingService(AppError(code, "nope"))) as client:
        response = client.get(path)

    assert response.status_code == status
    body = response.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == code
