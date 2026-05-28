import io

from flask import Flask

import app.routes as routes
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
