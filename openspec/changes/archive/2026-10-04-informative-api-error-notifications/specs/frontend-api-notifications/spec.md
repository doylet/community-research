## ADDED Requirements

### Requirement: Structured API errors are shown, not discarded
When the search API responds with a JSON error envelope, the frontend SHALL show the envelope's `error.message`, whatever the HTTP status. The frontend SHALL NOT replace that message with a generic status-only message.

#### Scenario: Invalid input returns 400 with a message
- **WHEN** the API responds `400` with `{"success": false, "error": {"code": "INVALID_INPUT", "message": "subreddit must contain letters, numbers, or underscores"}}`
- **THEN** the notification SHALL include the text "subreddit must contain letters, numbers, or underscores"

#### Scenario: 200 response with success false
- **WHEN** the API responds `200` with `success: false` and `error.code` set to `NOT_FOUND`
- **THEN** the frontend SHALL show the same notification it shows for a `404` with that code

### Requirement: Each API error code has a distinct notification
The frontend SHALL map each API error code to a notification with a title, a severity (`info`, `warning`, or `error`), a hint, and a retryable flag:
- `INVALID_INPUT`, `NOT_FOUND`, and `FORBIDDEN` SHALL be `warning` and not retryable.
- `UPSTREAM_RATE_LIMIT` and `UPSTREAM_UNAVAILABLE` SHALL be `info` and retryable.
- `AUTH_CONFIGURATION_ERROR` and `INTERNAL_ERROR` SHALL be `error`, not retryable, and their hint SHALL tell the user to report the problem with the request ID.

#### Scenario: Rate limit
- **WHEN** the API responds `429` with code `UPSTREAM_RATE_LIMIT`
- **THEN** the notification SHALL have severity `info`, SHALL say Reddit is rate-limiting requests, and SHALL offer a retry action

#### Scenario: Private subreddit
- **WHEN** the API responds `403` with code `FORBIDDEN`
- **THEN** the notification SHALL have severity `warning`, SHALL say the subreddit is not accessible, and SHALL NOT offer a retry action

#### Scenario: Server misconfiguration
- **WHEN** the API responds `401` with code `AUTH_CONFIGURATION_ERROR`
- **THEN** the notification SHALL have severity `error` and SHALL state that the problem is not caused by the user's search

#### Scenario: Every backend code is covered
- **WHEN** a code is defined in `app/errors.py` `ErrorCode`
- **THEN** the frontend error table SHALL contain an entry for that code

### Requirement: Diagnostic details are shown
Every failure notification SHALL show the HTTP status (when a response was received), the error code (when present), and the `request_id` (when present).

#### Scenario: Envelope with request ID
- **WHEN** the API responds `500` with code `INTERNAL_ERROR` and `request_id` `3f2a9c1e-…`
- **THEN** the notification details SHALL include `HTTP 500`, `INTERNAL_ERROR`, and the request ID

#### Scenario: No response received
- **WHEN** the request fails before any response is received
- **THEN** the notification SHALL omit the status, code, and request ID instead of showing placeholder values

### Requirement: Responses without a usable envelope are classified by status
If the response body is not valid JSON, or its `error.code` is not recognised, the frontend SHALL classify the failure by HTTP status: `400`, `403`, `404`, and `429` SHALL use the same notification as their matching code; `502`, `503`, and `504` SHALL use the upstream-unavailable notification; any other status SHALL produce an "unexpected response" notification that includes the status. The "unexpected response" notification SHALL be retryable exactly when the status is 500 or higher.

#### Scenario: Gateway HTML page
- **WHEN** the API responds `502` with an HTML body
- **THEN** the notification SHALL use the upstream-unavailable wording, show `HTTP 502`, and offer a retry action

#### Scenario: Unknown code
- **WHEN** the API responds `418` with `error.code` set to `SOMETHING_NEW` and a message
- **THEN** the notification SHALL say the response was unexpected, show `HTTP 418` and the API's message, and SHALL NOT offer a retry action

### Requirement: Timeouts and network failures are told apart
The search request SHALL time out after 45 seconds. A timeout SHALL produce a retryable `info` notification that says the API may be waking up. A network failure that receives no response SHALL produce a retryable `error` notification that names the API base URL the frontend tried to reach.

#### Scenario: Cold start exceeds the timeout
- **WHEN** the API does not respond within 45 seconds
- **THEN** the page SHALL render a notification saying the API is taking too long and may be waking up, with a retry action

#### Scenario: API unreachable
- **WHEN** the connection to the API is refused
- **THEN** the notification SHALL say the API could not be reached and SHALL include the configured API base URL

### Requirement: Retry re-runs the same search
A retryable notification SHALL include a "Try again" link to the current page URL with the same `subreddit`, `query`, `sort`, and `limit` parameters. The link SHALL work without client-side JavaScript.

#### Scenario: Retry after rate limit
- **WHEN** the user follows "Try again" on a rate-limit notification for `subreddit=python&query=agents&sort=top&limit=12`
- **THEN** the browser SHALL request the page with those same four parameters

### Requirement: Empty results are not shown as an error
A successful response with zero posts SHALL show a neutral `status` notice that names the subreddit and query searched. It SHALL NOT use error styling.

#### Scenario: No matches
- **WHEN** the API responds `200` with `success: true` and `data: []` for subreddit `python` and query `xyzzy`
- **THEN** the page SHALL show a notice naming `r/python` and `xyzzy` and suggesting a broader query or another sort

### Requirement: Notifications are accessible
Notifications with severity `error` SHALL use `role="alert"`. Notifications with severity `info` or `warning`, and the empty-results notice, SHALL use `role="status"`. Severity SHALL be shown by an icon and a title as well as by colour.

#### Scenario: Error severity
- **WHEN** an `INTERNAL_ERROR` notification renders
- **THEN** its container SHALL have `role="alert"` and SHALL contain an icon and a title
