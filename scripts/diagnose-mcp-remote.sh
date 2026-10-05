#!/usr/bin/env bash
set -euo pipefail

MCP_URL="${1:-https://community-research-mcp.onrender.com/mcp}"
MCP_REMOTE_VERSION="${MCP_REMOTE_VERSION:-0.1.38}"
MCP_REMOTE_PACKAGE="mcp-remote@${MCP_REMOTE_VERSION}"

cat <<EOF
Running mcp-remote diagnostics
- URL: ${MCP_URL}
- Package: ${MCP_REMOTE_PACKAGE}
EOF

# Use a short run with JSON-RPC initialize + tools/list over stdio.
# This is useful for reproducing transport/proxy issues outside Claude Desktop.
{
  printf '%s\n' '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{"extensions":{"io.modelcontextprotocol/ui":{"mimeTypes":["text/html;profile=mcp-app"]}}},"clientInfo":{"name":"diagnose-mcp-remote","version":"1.0.0"}}}'
  printf '%s\n' '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
  sleep 1
} | DEBUG=mcp-remote* npx -y "${MCP_REMOTE_PACKAGE}" "${MCP_URL}" --transport http-only
