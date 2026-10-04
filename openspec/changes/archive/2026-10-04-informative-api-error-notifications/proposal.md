## Why

When a search fails, the frontend discards the API's structured error and shows a generic line such as "Search failed with status 400." The API already returns an error `code`, a human-readable `message`, and a `request_id` for every failure. The user cannot tell a typo in the subreddit name from a Reddit rate limit, a private subreddit, a server misconfiguration, or a Render cold start, so they do not know whether to fix their input, wait, or report a problem.

## What Changes

- The search page reads the JSON error envelope on non-2xx responses instead of discarding it, and shows the API's `message`.
- Each API error code (`INVALID_INPUT`, `NOT_FOUND`, `FORBIDDEN`, `AUTH_CONFIGURATION_ERROR`, `UPSTREAM_RATE_LIMIT`, `UPSTREAM_UNAVAILABLE`, `INTERNAL_ERROR`) maps to a notification with a title, a severity, and a suggested next step (fix input, try again shortly, or report the problem).
- Each notification shows the HTTP status, the error code, and the `request_id` in a details line, so the user can quote it in a bug report.
- The search page handles three failures that currently share one catch-all message:
  - a response whose body is not JSON, such as a Render 502 HTML page
  - a request that times out, for example while the API is waking from a cold start
  - a network failure where the API cannot be reached
- Notifications for retryable failures include a "Try again" action that re-runs the same search.
- An empty result set keeps its own neutral notice and names the subreddit and query that returned nothing.

No API changes. The response envelope and status mapping in `app/routes.py` stay as they are.

## Capabilities

### New Capabilities
- `frontend-api-notifications`: How the frontend turns API responses (success, structured errors, malformed responses, timeouts, network failures) into user-facing notifications.

### Modified Capabilities
_None._ `service-endpoints` covers which API URL the frontend uses, not how it presents responses.

## Impact

- **Code**: `frontend/app/page.tsx` (search fetch and rendering). Error classification and notification rendering move into a new `frontend/lib/api-errors.ts` and a new `frontend/components/api-notification.tsx`.
- **API**: none. The frontend depends on the existing envelope (`success`, `request_id`, `data`, `error.code`, `error.message`) and on the status mapping in `_status_code_for_error`.
- **Dependencies**: none new. Icons come from the existing `lucide-react` dependency.
- **Out of scope**: the "Inspect Thread JSON" and "Download CSV" links. They open API URLs directly in a new tab, so the frontend never sees those responses.
