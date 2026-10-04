## 1. Fix

- [x] 1.1 In `app/errors.py`, map `prawcore.exceptions.Redirect` to `AppError(ErrorCode.NOT_FOUND, "Subreddit was not found")`. Place it next to the `NotFound` branch, before the generic `ResponseException` branch.

## 2. Tests

- [x] 2.1 In `tests/test_reddit_service.py`, add a test: a search whose fake client raises `Redirect`, with `retry_attempts=3`, fails with `NOT_FOUND` and message "Subreddit was not found", is not retryable, and is attempted once.
- [x] 2.2 Run the full pytest suite.

## 3. Verify

- [x] 3.1 With a read-only praw client, confirm that the real `Redirect` from searching a nonexistent subreddit now maps to `NOT_FOUND`.
