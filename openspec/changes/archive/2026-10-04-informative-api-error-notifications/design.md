## Context

`frontend/app/page.tsx` is a Next.js server component. It calls `GET {api}/api/search_posts` while rendering and collapses every failure into one of three strings:

```
response.ok == false   → "Search failed with status {n}."   (body discarded)
success == false       → error.message ?? "Search failed."
fetch throws           → "Could not reach the API service."
```

The Flask API already returns a consistent envelope for every failure (`app/mcp_response.py`):

```json
{ "success": false, "request_id": "…", "data": null,
  "error": { "code": "UPSTREAM_RATE_LIMIT", "message": "Reddit API rate limit exceeded" },
  "meta": { "retries": 0, "version": "v1" } }
```

Error codes map to HTTP statuses in `app/routes.py::_status_code_for_error`:

| code | status | retryable on the server |
|---|---|---|
| INVALID_INPUT | 400 | no |
| AUTH_CONFIGURATION_ERROR | 401 | no |
| FORBIDDEN | 403 | no |
| NOT_FOUND | 404 | no |
| UPSTREAM_RATE_LIMIT | 429 | no |
| UPSTREAM_UNAVAILABLE | 503 | yes (the server already retried with backoff) |
| INTERNAL_ERROR | 500 | no |

The envelope does not include the server's `retryable` flag, and the frontend has no test runner. Render's free tier can take close to a minute to wake the API, and the frontend `fetch` has no timeout, so a cold start shows up as a page that hangs.

## Goals / Non-Goals

**Goals:**
- Every failed search tells the user what went wrong, whose side it is on (theirs, Reddit's, or the service's), and what to do next.
- Every failure exposes the HTTP status, error code, and `request_id` for debugging.
- Malformed responses, timeouts, and network failures are told apart.
- The mapping from response to notification is a pure function with unit tests.

**Non-Goals:**
- Changing the API envelope, status codes, or error messages.
- Toast or client-side notification infrastructure. The page stays server-rendered with no client JavaScript.
- Handling the "Inspect Thread JSON" and "Download CSV" links, which open API URLs directly.
- Client-side form validation.

## Decisions

### 1. Classify the response in a pure function, `frontend/lib/api-errors.ts`

```
fetch outcome ──▶ classifyApiFailure(input) ──▶ ApiNotification
                                                  { kind, severity, title, message,
                                                    hint, retryable, status?, code?,
                                                    requestId? }
```

`input` is a discriminated union: `{ type: "http", status, body }` where `body` is the parsed JSON or `null`, `{ type: "timeout" }`, or `{ type: "network" }`. The fetch wrapper in `page.tsx` only gathers facts. All wording and severity decisions live in the classifier.

*Alternative:* branch inline in `page.tsx`. That is harder to test, and the page already mixes data fetching with a lot of markup.

### 2. The code-to-notification table lives in the frontend

| code | severity | title | hint | retryable |
|---|---|---|---|---|
| INVALID_INPUT | warning | Check your search | Adjust the search and try again. | no |
| NOT_FOUND | warning | Subreddit not found | Check the spelling of r/{subreddit}. | no |
| FORBIDDEN | warning | Subreddit is not accessible | It may be private, quarantined, or banned. | no |
| UPSTREAM_RATE_LIMIT | info | Reddit is rate-limiting requests | Wait about a minute, then try again. | yes |
| UPSTREAM_UNAVAILABLE | info | Reddit is temporarily unavailable | Try again in a few moments. | yes |
| AUTH_CONFIGURATION_ERROR | error | Service configuration problem | This is not caused by your search. Report it with the request ID. | no |
| INTERNAL_ERROR | error | Something went wrong on our side | Report it with the request ID. | no |
| *(timeout)* | info | The API is taking too long | It may be waking up. Try again in a few seconds. | yes |
| *(network)* | error | Could not reach the API | Check that the API is running at {source}. | yes |
| *(non-JSON or unknown code)* | error | Unexpected response (HTTP {status}) | Try again. If it keeps happening, report it. | yes if status ≥ 500 |

The message line always shows the API's own `error.message` when one is present, because it is often more specific (for example, "sort must be one of: …"). The title and hint add the frontend's context around it.

*Alternative:* add `retryable` and `hint` to the API envelope. That makes this a cross-service change touching the MCP contract tests. The frontend can derive both from `code`, so the API stays untouched. If the MCP clients later need hints, the table can move server-side.

### 3. Fall back to the HTTP status when the body has no recognised code

Parse the JSON body whatever the status. If the parse fails or `error.code` is not recognised, classify by HTTP status: 400 → INVALID_INPUT, 404 → NOT_FOUND, 403 → FORBIDDEN, 429 → UPSTREAM_RATE_LIMIT, 502/503/504 → UPSTREAM_UNAVAILABLE-like wording, and anything else → the "unexpected response" entry. This covers Render's own HTML error pages and gateway 502s, which never contain the envelope.

A 200 with `success: false` is classified by its code the same way as a non-2xx response.

### 4. Time out the server-side fetch after 45 seconds

Use `AbortSignal.timeout(45_000)` and report `TimeoutError` as the timeout case. 45 seconds covers most Render cold starts and stops the page hanging indefinitely. The value is a named constant in `api-errors.ts`.

*Alternative:* a short timeout (around 10 seconds) with an automatic retry. That adds hidden latency and quota usage, and a cold start would still need a second attempt.

### 5. "Try again" is a plain link

The page is a GET form, so the current URL fully describes the search. "Try again" links to the same query string, so a retry is just a re-render. No client JavaScript is needed.

### 6. Rendering: `frontend/components/api-notification.tsx`

This is a server component that takes an `ApiNotification`. It renders a bordered panel styled by severity (info cyan, warning amber, error rose) with a `lucide-react` icon. The panel holds the title, the message, the hint, an optional "Try again" link, and a small monospace details line: `HTTP 429 · UPSTREAM_RATE_LIMIT · request 3f2a…`. The panel uses `role="alert"` for errors and `role="status"` for info and warning severities.

The empty-results notice becomes a `status` panel that names the subreddit and query.

### 7. Unit tests run with Node's built-in runner

`frontend/lib/api-errors.test.ts` runs with `node --test` through a new `npm test` script. Node 22.6+ strips TypeScript types natively, and Node 26 is installed locally, so no new dependencies are needed. `api-errors.ts` therefore uses no path aliases or non-type imports.

*Alternative:* Vitest. It is the better long-term choice if the frontend gains more logic, but one pure module does not justify it yet.

## Risks / Trade-offs

- **[The frontend table drifts from API error codes]** → Unknown codes fall back to status-based classification, so a new code still produces a sensible notification. A test asserts that every code in `app/errors.py::ErrorCode` has a table entry, mirroring the hostname check in `tests/test_service_endpoints.py`.
- **[A 45-second timeout still feels long]** → The timeout notification explains the likely cause. A loading state would need client components and is out of scope.
- **[`request_id` is shown to end users]** → It is a random UUID with no sensitive content, and it is already in every response body.
- **[Render runs a different Node version from the one running `node --test`]** → Tests run locally and in CI only, and the production build is unaffected. `engines` is not changed.
- **[`AbortSignal.timeout` interacts badly with Next's fetch caching]** → The fetch already uses `cache: "no-store"`. Verify against `next build` output.

## Migration Plan

Frontend-only and stateless. Deploy the `community-research` Render service as usual. To roll back, revert the commit.

## Open Questions

- Should `INVALID_INPUT` highlight the specific form field? The API message names the parameter (`subreddit`, `query`, `sort`, `limit`), so this is cheap. It is listed as an optional task, not a requirement.
