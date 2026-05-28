## Context

The repository currently has a working MCP server (`mcp_server.py`) and Flask routes (`app/routes.py`) that both fetch Reddit data. Data retrieval and normalization logic are duplicated across these paths. Reddit credentials are loaded from environment variables in `app/reddit.py`, but configuration validation, secret-safe diagnostics, and consistent runtime error behavior are not centralized. The change needs to preserve existing functionality while introducing structured MCP responses, cleaner credential/token handling, and stronger reliability guarantees.

## Goals / Non-Goals

**Goals:**
- Provide a stable structured response envelope for all MCP tool outputs.
- Ensure valid input yields predictable structured data across thread and search operations.
- Centralize credential/token configuration and validation for Reddit access.
- Eliminate duplicate Reddit extraction logic by introducing a shared service layer.
- Improve reliability with typed errors, bounded retries, and deterministic input/output limits.
- Add tests that validate success and failure contracts.

**Non-Goals:**
- Building frontend integrations or UX changes.
- Adding advanced NLP/sentiment analysis pipelines.
- Supporting write operations to Reddit (posting, voting, moderation).
- Introducing multi-tenant credential stores or external secret managers in this phase.

## Decisions

1. Shared service boundary for Reddit operations
- Decision: Introduce a shared Reddit service module that performs input validation, calls PRAW, and normalizes output data.
- Rationale: Removes duplication between MCP and Flask endpoints and creates one correctness surface.
- Alternatives considered:
  - Keep logic in each endpoint: faster short term, but increases divergence and defects.
  - Move all functionality into MCP only: breaks existing Flask route usage.

2. Standard response envelope for MCP tools
- Decision: Every MCP tool returns the same top-level shape: `success`, `request_id`, `data`, `error`, `meta`.
- Rationale: Downstream agents can parse all tool responses uniformly and handle failures consistently.
- Alternatives considered:
  - Keep raw list/dict payloads per tool: simpler now, harder to consume reliably.
  - Raise exceptions directly to caller: loses typed error semantics and consistency.

3. Centralized config and startup validation
- Decision: Add a configuration layer that reads required Reddit credentials from environment variables once and validates them during startup.
- Rationale: Prevents late runtime failures and improves operability.
- Alternatives considered:
  - Lazy-read env vars in each call: allows hidden misconfiguration and inconsistent behavior.
  - Hardcode defaults for credentials: unsafe and operationally brittle.

4. Secret-safe diagnostics
- Decision: Log and return only sanitized configuration errors, never raw credential values.
- Rationale: Protects secrets in logs and tool responses.
- Alternatives considered:
  - Include full env values for debugging: unacceptable leakage risk.

5. Bounded reliability policy
- Decision: Apply bounded retry with short exponential backoff for transient upstream failures and explicit timeout limits for API operations.
- Rationale: Reduces intermittent failures while preventing hung tool calls.
- Alternatives considered:
  - No retries: simpler but less resilient.
  - Unbounded retries: can stall or overload callers.

6. Deterministic error taxonomy
- Decision: Map failures to stable error codes (`INVALID_INPUT`, `AUTH_CONFIGURATION_ERROR`, `UPSTREAM_RATE_LIMIT`, `UPSTREAM_UNAVAILABLE`, `INTERNAL_ERROR`).
- Rationale: Makes failures testable and automatable for clients.
- Alternatives considered:
  - Pass through library exceptions directly: unstable and implementation-coupled.

## Risks / Trade-offs

- [Risk] Envelope migration may affect existing MCP clients expecting raw arrays. -> Mitigation: Version tool contracts in change docs and provide examples in tests.
- [Risk] Retry policy could mask persistent upstream issues and add latency. -> Mitigation: Keep retry count low and include retry metadata in `meta`.
- [Risk] Shared service refactor might regress Flask CSV behavior. -> Mitigation: Preserve existing output columns and add route-level regression tests.
- [Risk] Strict input validation may reject some legacy caller formats. -> Mitigation: Document accepted input forms and return actionable `INVALID_INPUT` messages.

## Migration Plan

1. Add shared configuration and Reddit service modules while keeping existing endpoints unchanged.
2. Move MCP tools to use shared service and response envelope.
3. Update Flask routes to use shared service without changing endpoint purpose.
4. Add contract and error-path tests for MCP tools and regression tests for route CSV output.
5. Validate startup behavior with missing credentials and ensure sanitized error reporting.
6. Rollback strategy: revert to previous MCP tool handlers and route-specific extraction logic if blocking regressions appear.

## Open Questions

- Should the structured envelope include a `version` field in `meta` for explicit contract versioning in v1?
- Should request IDs be caller-provided (for correlation) or always server-generated?
- Should subreddit search support optional post time-window filtering in this phase or defer to a follow-on change?
