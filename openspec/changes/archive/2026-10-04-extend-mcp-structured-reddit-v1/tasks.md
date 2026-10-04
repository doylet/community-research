## 1. Shared Configuration and Service Foundation

- [x] 1.1 Add centralized runtime configuration module for Reddit credentials and MCP reliability settings (timeouts, retry limits, bounds).
- [x] 1.2 Implement startup validation for required credentials with sanitized configuration errors.
- [x] 1.3 Create shared Reddit service module for thread retrieval and subreddit search normalization.
- [x] 1.4 Refactor existing Reddit client initialization to be consumed through the centralized configuration path.

## 2. MCP Tool Contract and Reliability Controls

- [x] 2.1 Define and implement a standard MCP response envelope (`success`, `request_id`, `data`, `error`, `meta`) for all tools.
- [x] 2.2 Update thread retrieval MCP tool to use shared service, input validation, and bounded output normalization.
- [x] 2.3 Update subreddit search MCP tool to enforce parameter bounds and return normalized structured data.
- [x] 2.4 Implement deterministic error mapping for `INVALID_INPUT`, `AUTH_CONFIGURATION_ERROR`, `UPSTREAM_RATE_LIMIT`, `UPSTREAM_UNAVAILABLE`, and `INTERNAL_ERROR`.
- [x] 2.5 Add bounded retry/backoff and timeout handling for transient Reddit API failures.

## 3. Flask Route Integration and Regression Safety

- [x] 3.1 Refactor Flask thread export route to consume the shared Reddit service without changing endpoint purpose.
- [x] 3.2 Ensure CSV output schema remains compatible with current downstream expectations.
- [x] 3.3 Add regression checks to confirm route behavior remains stable after refactor.

## 4. Verification and Documentation

- [x] 4.1 Add MCP contract tests validating envelope shape for success and failure responses.
- [x] 4.2 Add tests for input validation boundaries and deterministic error code mapping.
- [x] 4.3 Add tests for retry/timeout behavior under simulated upstream failures.
- [x] 4.4 Update developer documentation for required environment variables, startup validation behavior, and MCP response contract examples.
