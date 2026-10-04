## Why

Searching a subreddit that does not exist returns `503 UPSTREAM_UNAVAILABLE` instead of `404 NOT_FOUND`. Reddit answers with a redirect to `/subreddits/search`, which praw raises as `prawcore.exceptions.Redirect`. `map_reddit_exception` has no branch for it, so it falls through to the generic availability branch and is marked retryable. Two problems follow:

- **Wrong message.** The user is told Reddit is down when the subreddit name is wrong. The frontend shows "Reddit is temporarily unavailable" with a "Try again" link that can never succeed.
- **Wasted quota.** The API retries a request that cannot succeed, up to `retry_attempts` times with backoff. This goes against the `reddit-upstream-efficiency` capability.

## What Changes

- `map_reddit_exception` maps `prawcore.exceptions.Redirect` to `NOT_FOUND` with the message "Subreddit was not found", non-retryable. The check sits before the generic `ResponseException` branch.
- `/api/search_posts` for a nonexistent subreddit returns 404 with the standard error envelope, after a single upstream attempt.

## Capabilities

### New Capabilities
_None._

### Modified Capabilities
- `reddit-upstream-efficiency`: the "Not-Found and Forbidden Error Classification" requirement now covers Reddit redirects (nonexistent subreddits) as `NOT_FOUND`.

## Impact

- **Code:** `app/errors.py` (one new branch).
- **Tests:** `tests/test_reddit_service.py` (Redirect is classified as not-found and not retried on search).
- **API:** a search on a nonexistent subreddit changes from 503 to 404, with code `NOT_FOUND` instead of `UPSTREAM_UNAVAILABLE`. The envelope shape is unchanged. MCP clients receive `NOT_FOUND` through the existing pass-through.
- **Frontend:** no change. It already shows "Subreddit not found" for `NOT_FOUND`.
