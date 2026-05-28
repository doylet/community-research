from app.config import RuntimeConfig
from app.errors import AppError, ErrorCode
from app.reddit_service import RedditService


class FakeComments:
    def __init__(self, comments):
        self._comments = comments

    def replace_more(self, limit=None):
        return None

    def list(self):
        return self._comments


class FakeComment:
    def __init__(self, cid):
        self.author = "author"
        self.body = "text"
        self.score = 1
        self.id = cid
        self.parent_id = "t3_parent"
        self.created_utc = 1
        self.permalink = "/r/test/comments/test/comment"


class FakeSubmission:
    def __init__(self, sid):
        self.author = "poster"
        self.title = "hello"
        self.selftext = "world"
        self.score = 10
        self.id = sid
        self.created_utc = 1
        self.permalink = "/r/test/comments/test/post"
        self.comments = FakeComments([FakeComment("c1"), FakeComment("c2")])


class FakeClientSuccess:
    def submission(self, id):
        return FakeSubmission(id)

    def subreddit(self, name):
        class _Subreddit:
            def search(self, query, sort, limit):
                return []

        return _Subreddit()


def build_config(retry_attempts=3):
    return RuntimeConfig(
        reddit_client_id="id",
        reddit_client_secret="secret",
        reddit_user_agent="agent",
        reddit_username=None,
        reddit_password=None,
        mcp_port=8000,
        upstream_timeout_seconds=10,
        retry_attempts=retry_attempts,
        retry_backoff_seconds=0.001,
        max_comments=5,
        min_search_limit=1,
        max_search_limit=100,
    )


def test_invalid_thread_id_returns_invalid_input():
    service = RedditService(config=build_config(), reddit_client_factory=lambda cfg: FakeClientSuccess())

    try:
        service.fetch_thread_records("bad!")
        assert False, "Expected AppError"
    except AppError as exc:
        assert exc.code == ErrorCode.INVALID_INPUT


def test_search_limit_bounds_are_enforced():
    service = RedditService(config=build_config(), reddit_client_factory=lambda cfg: FakeClientSuccess())

    try:
        service.search_posts("python", "query", 0)
        assert False, "Expected AppError"
    except AppError as exc:
        assert exc.code == ErrorCode.INVALID_INPUT


def test_retry_succeeds_after_transient_upstream_failures():
    attempts = {"count": 0}

    class FakeClientRetry:
        def submission(self, id):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "temporary", retryable=True)
            return FakeSubmission(id)

        def subreddit(self, name):
            raise NotImplementedError

    service = RedditService(config=build_config(retry_attempts=3), reddit_client_factory=lambda cfg: FakeClientRetry())

    result = service.fetch_thread_records("abc123")

    assert result.retries == 2
    assert len(result.data) == 3


def test_retry_exhaustion_returns_upstream_unavailable():
    class FakeClientAlwaysFail:
        def submission(self, id):
            raise AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "temporary", retryable=True)

        def subreddit(self, name):
            raise NotImplementedError

    service = RedditService(config=build_config(retry_attempts=2), reddit_client_factory=lambda cfg: FakeClientAlwaysFail())

    try:
        service.fetch_thread_records("abc123")
        assert False, "Expected AppError"
    except AppError as exc:
        assert exc.code == ErrorCode.UPSTREAM_UNAVAILABLE
