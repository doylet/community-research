import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

from .config import RuntimeConfig, get_runtime_config, validate_runtime_config
from .errors import AppError, ErrorCode, map_reddit_exception
from .reddit import get_reddit_client

THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{5,10}$")
SUBREDDIT_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,21}$")
VALID_SORTS = {"relevance", "hot", "top", "new", "comments"}


@dataclass
class ServiceResult:
    data: list[dict]
    retries: int


class RedditService:
    def __init__(
        self,
        config: RuntimeConfig | None = None,
        reddit_client_factory: Callable[..., object] = get_reddit_client,
    ):
        self._config = config or get_runtime_config()
        validate_runtime_config(self._config)
        self._reddit_client_factory = reddit_client_factory

    def _client(self):
        return self._reddit_client_factory(self._config)

    def _run_with_retry(self, operation: Callable[[], list[dict]]) -> ServiceResult:
        retries = 0
        for attempt in range(1, self._config.retry_attempts + 1):
            try:
                return ServiceResult(data=operation(), retries=retries)
            except Exception as exc:
                mapped = map_reddit_exception(exc)
                if not mapped.retryable or attempt >= self._config.retry_attempts:
                    raise mapped
                retries += 1
                backoff = self._config.retry_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(backoff)

        raise AppError(ErrorCode.INTERNAL_ERROR, "Retry loop exited unexpectedly")

    def fetch_thread_records(self, thread_id: str, max_comments: int | None = None, include_url: bool = True) -> ServiceResult:
        if not THREAD_ID_PATTERN.match(thread_id):
            raise AppError(ErrorCode.INVALID_INPUT, "thread_id must be an alphanumeric Reddit submission id")

        comment_limit = max_comments if max_comments is not None else self._config.max_comments
        if comment_limit < 1:
            raise AppError(ErrorCode.INVALID_INPUT, "max_comments must be at least 1")

        def operation() -> list[dict]:
            reddit = self._client()
            submission = reddit.submission(id=thread_id)
            submission.comments.replace_more(limit=None)

            results: list[dict] = []
            post_row = {
                "type": "post",
                "author": str(submission.author),
                "text": submission.title + ("\n\n" + submission.selftext if submission.selftext else ""),
                "score": submission.score,
                "id": submission.id,
                "parent_id": None,
                "created_utc": submission.created_utc,
            }
            if include_url:
                post_row["url"] = f"https://reddit.com{submission.permalink}"
            results.append(post_row)

            comments = submission.comments.list()
            for comment in comments[:comment_limit]:
                row = {
                    "type": "comment",
                    "author": str(comment.author),
                    "text": comment.body,
                    "score": comment.score,
                    "id": comment.id,
                    "parent_id": comment.parent_id,
                    "created_utc": comment.created_utc,
                }
                if include_url:
                    row["url"] = f"https://reddit.com{comment.permalink}"
                results.append(row)

            return results

        return self._run_with_retry(operation)

    def search_posts(self, subreddit: str, query: str, limit: int, sort: str = "relevance") -> ServiceResult:
        if not SUBREDDIT_PATTERN.match(subreddit):
            raise AppError(ErrorCode.INVALID_INPUT, "subreddit must contain letters, numbers, or underscores")
        if not query.strip():
            raise AppError(ErrorCode.INVALID_INPUT, "query must not be empty")
        if sort not in VALID_SORTS:
            raise AppError(ErrorCode.INVALID_INPUT, "sort must be one of: relevance, hot, top, new, comments")
        if not (self._config.min_search_limit <= limit <= self._config.max_search_limit):
            raise AppError(
                ErrorCode.INVALID_INPUT,
                f"limit must be between {self._config.min_search_limit} and {self._config.max_search_limit}",
            )

        def operation() -> list[dict]:
            reddit = self._client()
            subreddit_obj = reddit.subreddit(subreddit)

            results: list[dict] = []
            for submission in subreddit_obj.search(query, sort=sort, limit=limit):
                results.append({
                    "id": submission.id,
                    "title": submission.title,
                    "author": str(submission.author),
                    "score": submission.score,
                    "url": f"https://reddit.com{submission.permalink}",
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "selftext": submission.selftext[:500] if submission.selftext else "",
                })
            return results

        return self._run_with_retry(operation)


@lru_cache(maxsize=1)
def get_shared_reddit_service() -> RedditService:
    return RedditService()
