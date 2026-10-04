## Context

`map_reddit_exception` in `app/errors.py` checks specific `prawcore` exceptions (`TooManyRequests`, `NotFound`, `Forbidden`, `OAuthException`) before a generic branch. That branch maps any `RequestException`, `ResponseException` or `ServerError` to retryable `UPSTREAM_UNAVAILABLE`. `prawcore.exceptions.Redirect` subclasses `ResponseException` and has no branch of its own.

The bug was reproduced with a read-only praw client: `subreddit("thisdoesnotexist9q8z7").search("hello")` raises `Redirect` with the message "Redirect to /subreddits/search". The same search on `python` succeeds.

## Goals / Non-Goals

**Goals:**
- A search on a nonexistent subreddit returns `NOT_FOUND` (404) after one upstream attempt.

**Non-Goals:**
- Telling apart the different redirect targets Reddit may use. Every `Redirect` this service can trigger comes from a subreddit lookup.
- Validating that a subreddit exists before searching. That would cost an extra upstream call on every search.

## Decisions

### Map every `Redirect` to `NOT_FOUND`, with a subreddit-specific message

The only Reddit calls that can redirect are subreddit lookups: search, and listings that resolve a subreddit name. Thread fetches by ID return 404 (`NotFound`), not a redirect. "Subreddit was not found" is more useful than the generic "Reddit resource was not found", and the frontend hint already names `r/{subreddit}`.

*Alternative:* inspect `exc.path` and only map `/subreddits/search`. That adds a dependency on Reddit's redirect URL for no practical gain. Any redirect is non-retryable either way.

### Place the branch next to `NotFound`

Keep it with the other specific `ResponseException` subclasses, before the generic branch. The existing comment there already explains why the order matters.

## Risks / Trade-offs

- **[Reddit uses a redirect for something other than a missing subreddit]** → The result would be a non-retryable `NOT_FOUND` instead of three retries of a request that would redirect again anyway. That is still the better outcome.
