## ADDED Requirements

### Requirement: Structured MCP Response Envelope
The MCP server MUST return a consistent top-level response envelope for every tool invocation.

#### Scenario: Successful tool response uses standard envelope
- **WHEN** a caller invokes a supported MCP tool with valid input and the operation succeeds
- **THEN** the response MUST include `success=true`, a non-empty `request_id`, a populated `data` object, `error=null`, and a `meta` object

#### Scenario: Failed tool response uses standard envelope
- **WHEN** a caller invokes a supported MCP tool and the operation fails
- **THEN** the response MUST include `success=false`, a non-empty `request_id`, `data=null`, a populated `error` object with a stable code, and a `meta` object

### Requirement: Validated Thread Retrieval
The MCP server MUST provide thread retrieval that returns normalized post and comment data for valid thread identifiers.

#### Scenario: Valid thread id returns normalized thread data
- **WHEN** a caller provides a valid Reddit thread identifier to thread retrieval
- **THEN** the response MUST include normalized post metadata and comment entries with stable field names

#### Scenario: Invalid thread id is rejected deterministically
- **WHEN** a caller provides a malformed or unsupported thread identifier
- **THEN** the server MUST return `success=false` with error code `INVALID_INPUT` and an actionable error message

### Requirement: Validated Subreddit Search
The MCP server MUST provide subreddit search with validated parameters and bounded result counts.

#### Scenario: Valid search returns bounded normalized results
- **WHEN** a caller provides a valid subreddit, query, and limit within allowed bounds
- **THEN** the server MUST return `success=true` with results normalized to a stable post schema and result count not exceeding the requested limit

#### Scenario: Out-of-range limit is rejected
- **WHEN** a caller provides a search limit outside the allowed range
- **THEN** the server MUST return `success=false` with error code `INVALID_INPUT`

### Requirement: Centralized Credential and Token Configuration
The system MUST load and validate required Reddit credentials and token-related settings from a centralized configuration component.

#### Scenario: Missing required credentials fails startup safely
- **WHEN** required Reddit credentials are absent at startup
- **THEN** the server MUST fail initialization with a sanitized configuration error that does not expose secret values

#### Scenario: Runtime components use centralized config
- **WHEN** MCP tools and route handlers execute Reddit operations
- **THEN** they MUST use the same centralized configuration and credential access path

### Requirement: Deterministic Error Taxonomy
The MCP server MUST map known failure modes to stable error codes that callers can handle programmatically.

#### Scenario: Upstream rate limit maps to stable code
- **WHEN** Reddit API responds with a rate-limit condition
- **THEN** the server MUST return error code `UPSTREAM_RATE_LIMIT`

#### Scenario: Upstream availability failures map to stable code
- **WHEN** Reddit API is unavailable or times out after retry policy is exhausted
- **THEN** the server MUST return error code `UPSTREAM_UNAVAILABLE`

### Requirement: Bounded Retry and Timeout Behavior
The MCP server MUST apply bounded retry and timeout controls for transient upstream failures.

#### Scenario: Transient failure is retried within configured bounds
- **WHEN** a transient upstream error occurs during a Reddit operation
- **THEN** the server MUST retry only up to configured maximum attempts and record retry metadata

#### Scenario: Timeout prevents hanging requests
- **WHEN** an upstream operation exceeds configured timeout limits
- **THEN** the server MUST terminate the operation and return `success=false` with a stable error code

### Requirement: Contract and Regression Verification
The project MUST include automated tests validating MCP response contracts and regression safety for shared Reddit logic.

#### Scenario: MCP contract tests validate envelope and error codes
- **WHEN** automated tests run for MCP tools
- **THEN** tests MUST verify both success and failure responses conform to the required envelope and stable error taxonomy

#### Scenario: Route regression tests preserve CSV behavior
- **WHEN** automated tests run for existing Flask thread export behavior
- **THEN** tests MUST confirm that CSV output structure remains compatible after shared service refactoring
