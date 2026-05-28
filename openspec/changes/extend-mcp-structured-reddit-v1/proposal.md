## Why

The current MCP server works for basic Reddit retrieval, but it does not yet provide a stable structured response contract, centralized secret/token handling, or reliability guardrails. This change is needed now to make the server reliably "just work" for valid inputs and predictable failures.

## What Changes

- Introduce a structured response envelope for all MCP tools, including success, data, error, and metadata fields.
- Add focused MCP tool coverage for Reddit thread retrieval and subreddit search with validated inputs and bounded outputs.
- Centralize Reddit credential and token configuration in a single configuration layer with startup validation and secret-safe error behavior.
- Refactor duplicated Reddit extraction logic into a shared service used by both MCP and existing Flask routes.
- Add robustness controls: deterministic error taxonomy, timeout/retry strategy for transient upstream failures, and contract tests for success and failure paths.

## Capabilities

### New Capabilities
- `mcp-reddit-server`: Structured Reddit MCP operations with validated inputs, centralized credential management, and reliability guardrails.

### Modified Capabilities
- None.

## Impact

- Affected code: `mcp_server.py`, `app/reddit.py`, `app/routes.py`, and new shared service/config/test modules.
- API impact: MCP tool outputs become standardized via a stable response envelope.
- Operational impact: startup fails fast on missing/invalid required credentials; errors are typed and safe for logs.
- Testing impact: adds contract and error-path validation for MCP tool behavior.
