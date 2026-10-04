## 1. Error classifier

- [x] 1.1 Create `frontend/lib/api-errors.ts` with the `ApiNotification` type, the `ApiFailureInput` union (`http` / `timeout` / `network`), and the `SEARCH_TIMEOUT_MS = 45_000` constant. Use no path aliases or runtime imports, so `node --test` can load the file directly.
- [x] 1.2 Add the code-to-notification table for all seven `ErrorCode` values (title, severity, hint, retryable), following design.md Decision 2.
- [x] 1.3 Implement `classifyApiFailure(input, context)`. `context` carries the subreddit and API base URL used in hints. Use the envelope's `error.code` when it is recognised, otherwise fall back to the HTTP status as in Decision 3. Always pass through `error.message` and `request_id` when present.
- [x] 1.4 Implement `formatNotificationDetails(n)`, which returns e.g. `HTTP 429 · UPSTREAM_RATE_LIMIT · request 3f2a…` and leaves out any missing parts.

## 2. Classifier tests

- [x] 2.1 Add `"test": "node --test \"lib/**/*.test.ts\""` to `frontend/package.json` scripts.
- [x] 2.2 Write `frontend/lib/api-errors.test.ts` covering:
  - every error code
  - a 200 response with `success: false`
  - a 502 with an HTML body
  - an unknown code with a 418 status
  - timeout and network failures
  - the details line with and without a status, code, and request ID
- [x] 2.3 Add `tests/test_frontend_error_codes.py`, which asserts that every `ErrorCode` attribute in `app/errors.py` appears as a key in `frontend/lib/api-errors.ts`.

## 3. Notification component

- [x] 3.1 Create `frontend/components/api-notification.tsx`, a server component that renders title, message, hint, details line, and an optional "Try again" link. Use severity styles (info cyan, warning amber, error rose) and `lucide-react` icons. Set `role="alert"` for errors and `role="status"` otherwise.
- [x] 3.2 Add an empty-results variant: a neutral `role="status"` notice that names `r/{subreddit}` and the query.

## 4. Wire into the search page

- [x] 4.1 Rewrite `searchPosts` in `frontend/app/page.tsx` to:
  - fetch with `signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS)`
  - always try to parse the JSON body
  - map `TimeoutError` to a timeout failure and other thrown errors to a network failure
  - return `{ posts, notification }`
- [x] 4.2 Build the "Try again" href from the resolved `subreddit`, `query`, `sort`, and `limit`, and pass it to `ApiNotification` when the notification is retryable.
- [x] 4.3 Replace the inline rose error section and the "No posts found" section with the new component.
- [x] 4.4 (Optional) For `INVALID_INPUT`, highlight the form field named in the API message (`subreddit`, `query`, `sort`, or `limit`).

## 5. Verify

- [x] 5.1 Run `npm test`, `npm run lint`, and `npm run build` in `frontend/`. Run `pytest tests/test_frontend_error_codes.py tests/test_service_endpoints.py`.
  - Done: `npm test` (20 passed), `npm run build`, `tsc --noEmit`, pytest (9 passed).
  - Lint: added `frontend/eslint.config.mjs` (Next.js `core-web-vitals` + `typescript` presets), plus `eslint`, `eslint-config-next`, and `@eslint/eslintrc` as dev dependencies. `npm run lint` passes with no warnings.
- [x] 5.2 Run the API locally on a free port (for example 8001) and start the frontend with `COMMUNITY_RESEARCH_API_URL=http://localhost:8001`. Check these by hand:
  - invalid subreddit (`?subreddit=bad-name!`) shows a 400 message
  - nonexistent subreddit
  - empty results
  - stopping the API shows the network notification
  - Done: invalid subreddit (400, field marked `aria-invalid`), API stopped (network notice), 502 HTML stub (upstream-unavailable notice, `HTTP 502`).
  - Local Reddit credentials are rejected (every search returns 401 `AUTH_CONFIGURATION_ERROR`, which renders correctly), so the last two checks ran against the production API:
    - Empty results show the neutral notice naming r/python and the query.
    - A nonexistent subreddit returns 503 `UPSTREAM_UNAVAILABLE` from the API, not 404 `NOT_FOUND`. The frontend renders that correctly. The cause is a backend bug: `prawcore.Redirect` falls through to the generic outage branch in `app/errors.py`. It is out of scope here (no API changes), so follow up in a separate change. Unit tests cover the frontend's `NOT_FOUND` notice.
- [x] 5.3 Point `COMMUNITY_RESEARCH_API_URL` at a port that accepts connections but never responds (for example `nc -l 8002`), and confirm the timeout notification appears after about 45 seconds.
