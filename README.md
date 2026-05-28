# Community Research

Backend service for Reddit community data retrieval with both Flask routes and an MCP server endpoint.

## Environment Variables

Required:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT

Optional:
- REDDIT_USERNAME
- REDDIT_PASSWORD
- PORT or MCP_PORT (default: 8000)
- REDDIT_TIMEOUT_SECONDS (default: 10)
- MCP_RETRY_ATTEMPTS (default: 3)
- MCP_RETRY_BACKOFF_SECONDS (default: 0.5)
- MCP_MAX_COMMENTS (default: 2000)
- MCP_MAX_SEARCH_LIMIT (default: 100)

Startup validates required credentials and fails with a sanitized error when missing.

## Running MCP Server

python mcp_server.py

Transport path:
- streamable-http on /mcp

## MCP Response Contract

All tools return the same response envelope:

{
  "success": true,
  "request_id": "uuid",
  "data": [ ... ],
  "error": null,
  "meta": {
    "retries": 0,
    "version": "v1"
  }
}

Failure shape:

{
  "success": false,
  "request_id": "uuid",
  "data": null,
  "error": {
    "code": "INVALID_INPUT",
    "message": "..."
  },
  "meta": {
    "retries": 0,
    "version": "v1"
  }
}

Error codes:
- INVALID_INPUT
- AUTH_CONFIGURATION_ERROR
- UPSTREAM_RATE_LIMIT
- UPSTREAM_UNAVAILABLE
- INTERNAL_ERROR

## Tests

python -m pytest
