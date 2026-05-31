# Community Research

Backend service for Reddit community data retrieval with both Flask routes and an MCP server endpoint.

The MCP process now calls the API service over HTTP. Reddit credentials stay in the API service environment only.

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

MCP-specific:
- COMMUNITY_RESEARCH_API_URL (required for MCP process)
- MCP_API_TIMEOUT_SECONDS (default: REDDIT_TIMEOUT_SECONDS)
- MCP_API_RETRY_ATTEMPTS (default: MCP_RETRY_ATTEMPTS)
- MCP_API_RETRY_BACKOFF_SECONDS (default: MCP_RETRY_BACKOFF_SECONDS)

Startup validates required Reddit credentials in the API service.

## Running MCP Server

python mcp_server.py

Transport path:
- streamable-http on /mcp

## Claude Desktop (Production)

To connect Claude Desktop to the production MCP endpoint, deploy the Render service named community-research-mcp and use an MCP HTTP bridge.

Production MCP URL:
- https://community-research-mcp.onrender.com/mcp

macOS Claude Desktop config file:
- ~/Library/Application Support/Claude/claude_desktop_config.json

Example config:

{
  "mcpServers": {
    "community-research-prod": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://community-research-mcp.onrender.com/mcp"
      ]
    }
  }
}

After saving config, fully quit and reopen Claude Desktop.

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
