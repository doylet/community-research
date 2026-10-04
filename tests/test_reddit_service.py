import pytest
from praw.models import MoreComments
from prawcore.exceptions import Forbidden, NotFound, Redirect, ServerError

from app.config import RuntimeConfig
from app.errors import AppError, ErrorCode
from app.reddit_service import RedditService


class FakeComments:
    def __init__(self, comments):
        self._comments = comments
        self.replace_more_calls = []

    def replace_more(self, limit=32):
        self.replace_more_calls.append(limit)
        self._comments = [c for c in self._comments if not isinstance(c, MoreComments)]
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


def build_config(retry_attempts=3, max_comments=5, replace_more_limit=32):
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
        max_comments=max_comments,
        min_search_limit=1,
        max_search_limit=100,
        replace_more_limit=replace_more_limit,
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


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.headers = {}
        self.text = ""


def make_more_comments():
    # Bypass PRAW's constructor; only isinstance checks matter here.
    return MoreComments.__new__(MoreComments)


class CountingFactory:
    def __init__(self, client):
        self.client = client
        self.calls = 0

    def __call__(self, cfg):
        self.calls += 1
        return self.client


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (NotFound(FakeResponse(404)), ErrorCode.NOT_FOUND),
        (Forbidden(FakeResponse(403)), ErrorCode.FORBIDDEN),
    ],
)
def test_not_found_and_forbidden_are_not_retried(exc, code):
    attempts = {"count": 0}

    class FakeClientRaises:
        def submission(self, id):
            attempts["count"] += 1
            raise exc

    service = RedditService(config=build_config(retry_attempts=3), reddit_client_factory=lambda cfg: FakeClientRaises())

    with pytest.raises(AppError) as exc_info:
        service.fetch_thread_records("abc123")

    assert exc_info.value.code == code
    assert exc_info.value.retryable is False
    assert attempts["count"] == 1


def test_server_error_is_still_retryable():
    attempts = {"count": 0}

    class FakeClientServerError:
        def submission(self, id):
            attempts["count"] += 1
            raise ServerError(FakeResponse(500))

    service = RedditService(config=build_config(retry_attempts=2), reddit_client_factory=lambda cfg: FakeClientServerError())

    with pytest.raises(AppError) as exc_info:
        service.fetch_thread_records("abc123")

    assert exc_info.value.code == ErrorCode.UPSTREAM_UNAVAILABLE
    assert attempts["count"] == 2


def test_nonexistent_subreddit_redirect_is_not_found_and_not_retried():
    attempts = {"count": 0}
    redirect_response = FakeResponse(302)
    redirect_response.headers = {"location": "https://www.reddit.com/subreddits/search.json?q=nosuchsub"}

    class FakeSubreddit:
        def search(self, query, sort, limit):
            attempts["count"] += 1
            raise Redirect(redirect_response)

    class FakeClientRedirects:
        def subreddit(self, name):
            return FakeSubreddit()

    service = RedditService(config=build_config(retry_attempts=3), reddit_client_factory=lambda cfg: FakeClientRedirects())

    with pytest.raises(AppError) as exc_info:
        service.search_posts(subreddit="nosuchsub", query="hello", limit=5)

    assert exc_info.value.code == ErrorCode.NOT_FOUND
    assert exc_info.value.message == "Subreddit was not found"
    assert exc_info.value.retryable is False
    assert attempts["count"] == 1


def test_client_is_built_lazily_and_reused():
    attempts = {"count": 0}

    class FlakyClient(FakeClientSuccess):
        def submission(self, id):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "temporary", retryable=True)
            return FakeSubmission(id)

    factory = CountingFactory(FlakyClient())
    service = RedditService(config=build_config(), reddit_client_factory=factory)
    assert factory.calls == 0

    service.fetch_thread_records("abc123")  # retried once
    service.fetch_thread_records("def456")
    service.search_posts("python", "query", 5)

    assert factory.calls == 1


def fetch_with_tree(comments, max_comments, replace_more_limit=32):
    submission = FakeSubmission("abc123")
    submission.comments = FakeComments(comments)

    class Client(FakeClientSuccess):
        def submission(self, id):
            return submission

    service = RedditService(
        config=build_config(max_comments=max_comments, replace_more_limit=replace_more_limit),
        reddit_client_factory=lambda cfg: Client(),
    )
    result = service.fetch_thread_records("abc123")
    return submission.comments.replace_more_calls, result


def test_enough_loaded_comments_skip_expansion():
    calls, result = fetch_with_tree([FakeComment("c1"), FakeComment("c2"), make_more_comments()], max_comments=2)

    assert calls == [0]
    assert len(result.data) == 3


def test_expansion_capped_by_default_limit():
    calls, _ = fetch_with_tree([FakeComment("c1"), make_more_comments()], max_comments=10)

    assert calls == [32]


def test_unlimited_expansion_opt_in():
    calls, _ = fetch_with_tree([FakeComment("c1"), make_more_comments()], max_comments=10, replace_more_limit=None)

    assert calls == [None]
