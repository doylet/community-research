## ADDED Requirements

### Requirement: Not-Found and Forbidden Error Classification
The system SHALL classify upstream Reddit "not found" responses as error code `NOT_FOUND` and "forbidden" responses as error code `FORBIDDEN`. Both SHALL be non-retryable, and these classifications SHALL take precedence over the generic `UPSTREAM_UNAVAILABLE` mapping.

#### Scenario: Nonexistent thread is not retried
- **WHEN** fetching a thread raises `prawcore.exceptions.NotFound` and `retry_attempts` is 3
- **THEN** the operation SHALL be attempted exactly once and SHALL fail with code `NOT_FOUND`

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

### Requirement: Reddit Client Reuse
A `RedditService` instance SHALL construct at most one Reddit client during its lifetime and SHALL reuse it across operations and retries.

#### Scenario: Multiple operations share a client
- **WHEN** a single `RedditService` performs two thread fetches and one search
- **THEN** its client factory SHALL have been invoked exactly once

#### Scenario: Lazy construction
- **WHEN** a `RedditService` is constructed but no operation is performed
- **THEN** its client factory SHALL NOT have been invoked

### Requirement: Bounded Comment Expansion
Thread retrieval SHALL limit the number of `MoreComments` expansion requests. It SHALL skip expansion entirely when the already-loaded comments meet the requested limit, and otherwise SHALL cap expansion at the configured `REDDIT_REPLACE_MORE_LIMIT` (default 32). Setting `REDDIT_REPLACE_MORE_LIMIT=none` SHALL allow unlimited expansion.

#### Scenario: Enough comments already loaded
- **WHEN** a thread fetch requests `max_comments=10` and the initial comment tree already contains at least 10 loaded comments
- **THEN** `replace_more` SHALL be called with `limit=0`, so that no additional network requests are made

#### Scenario: Expansion capped by configuration
- **WHEN** the initial tree has fewer loaded comments than requested and `REDDIT_REPLACE_MORE_LIMIT` is unset
- **THEN** `replace_more` SHALL be called with `limit=32`

#### Scenario: Unlimited expansion opt-in
- **WHEN** `REDDIT_REPLACE_MORE_LIMIT=none` and the initial tree has fewer loaded comments than requested
- **THEN** `replace_more` SHALL be called with `limit=None`

#### Scenario: Invalid configuration value
- **WHEN** `REDDIT_REPLACE_MORE_LIMIT` is set to a value that is neither a non-negative integer nor `none`
- **THEN** loading the runtime config SHALL raise a configuration error naming the variable

### Requirement: Legacy CSV Route Uses Structured Errors
The `/search` CSV route SHALL select its HTTP status from the structured error code of a failed operation, using the same mapping as the JSON API, and SHALL NOT include raw exception text in its response.

#### Scenario: Malformed thread id on CSV route
- **WHEN** `/search?id=bad!` is requested
- **THEN** the response status SHALL be 400

#### Scenario: Missing thread on CSV route
- **WHEN** `/search` is requested for a thread that raises `NOT_FOUND`
- **THEN** the response status SHALL be 404 with a human-readable message

#### Scenario: Unexpected failure on CSV route
- **WHEN** an unclassified exception occurs during a `/search` request
- **THEN** the response status SHALL be 500 and the body SHALL NOT contain the exception message
