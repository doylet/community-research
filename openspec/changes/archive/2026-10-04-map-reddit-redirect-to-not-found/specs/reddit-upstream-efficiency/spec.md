## MODIFIED Requirements

### Requirement: Not-Found and Forbidden Error Classification
The system SHALL classify upstream Reddit "not found" responses as error code `NOT_FOUND` and "forbidden" responses as error code `FORBIDDEN`. A Reddit redirect (`prawcore.exceptions.Redirect`), which Reddit returns when a subreddit does not exist, SHALL also be classified as `NOT_FOUND`. All of these SHALL be non-retryable, and these classifications SHALL take precedence over the generic `UPSTREAM_UNAVAILABLE` mapping.

#### Scenario: Nonexistent thread is not retried
- **WHEN** fetching a thread raises `prawcore.exceptions.NotFound` and `retry_attempts` is 3
- **THEN** the operation SHALL be attempted exactly once and SHALL fail with code `NOT_FOUND`

#### Scenario: Nonexistent subreddit is not retried
- **WHEN** a search raises `prawcore.exceptions.Redirect` and `retry_attempts` is 3
- **THEN** the operation SHALL be attempted exactly once and SHALL fail with code `NOT_FOUND` and the message "Subreddit was not found"

#### Scenario: Private subreddit returns forbidden
- **WHEN** a search raises `prawcore.exceptions.Forbidden`
- **THEN** the operation SHALL fail with code `FORBIDDEN` without retrying

#### Scenario: HTTP status codes for new error codes
- **WHEN** `/api/thread` or `/api/search_posts` fails with `NOT_FOUND` or `FORBIDDEN`
- **THEN** the HTTP status SHALL be 404 or 403 respectively, and the body SHALL use the standard error envelope

#### Scenario: Server errors remain retryable
- **WHEN** an operation raises `prawcore.exceptions.ServerError`
- **THEN** it SHALL still map to `UPSTREAM_UNAVAILABLE` with `retryable=true`

#### Scenario: MCP tools pass new codes through
- **WHEN** an MCP tool's upstream API call returns an error envelope with code `NOT_FOUND`
- **THEN** the MCP tool response SHALL contain `success=false` with error code `NOT_FOUND`
