# Errors and Limits

Every failed call returns `success: false` with `error.code` and `error.message`. Handle each code like this:

| Code | Meaning | What to do |
|---|---|---|
| `INVALID_INPUT` | A bad parameter: malformed thread ID, `limit` outside 1–100, unknown `sort`, or empty query. | Fix the input and retry once. For thread IDs, check that only the alphanumeric ID was passed, not the URL. |
| `NOT_FOUND` | The thread or subreddit does not exist. Reddit sends nonexistent subreddits to a search page, and the service maps that to this code. | Don't retry. Check the spelling of the subreddit, or try `subreddit=all`. Tell the user if a subreddit they named doesn't exist. |
| `FORBIDDEN` | The subreddit or thread is private, quarantined or banned. | Don't retry. Tell the user it can't be reached and continue with the other sources. |
| `UPSTREAM_RATE_LIMIT` | Reddit's rate limit was hit. | Wait briefly and retry once. If it fails again, stop fetching, report on what was already collected, and say the sample is smaller than planned. |
| `UPSTREAM_UNAVAILABLE` | Reddit or the API service could not be reached or timed out. | Retry once. The hosted service may be cold-starting, and the first call after it has been idle can take 30–60 seconds. If it still fails, tell the user the service is unavailable. |
| `AUTH_CONFIGURATION_ERROR` | The service's Reddit credentials are misconfigured. | Don't retry. Tell the user the Community Research service needs its Reddit credentials fixed. Nothing on the user's side can fix this. |
| `INTERNAL_ERROR` | An unexpected failure. | Retry once. If it persists, give the user the `request_id` so the maintainers can trace it. |

## Practical limits

- **Search limit:** at most 100 results per call. Run several narrower searches rather than one broad one.
- **Search snippet:** `selftext` holds only the first 500 characters. Fetch the thread to read the full post.
- **Comment cap:** `max_comments` defaults to 2000. Very large threads can take a while to fetch. Use a lower cap when skimming many threads.
- **No time filter:** sort by `new` and filter on `created_utc` yourself.
- **No user or subreddit metadata tools:** there is no tool for subscriber counts or user history. Estimate how active a subreddit is from the number of matching posts, their comment counts and their dates.
- **Cold start:** the hosted service sleeps when idle. A slow or failed first call doesn't mean the service is down.
