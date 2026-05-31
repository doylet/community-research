#!/usr/bin/env bash
set -euo pipefail

SERVER_NAME="fetch-reddit"
MCP_URL="${1:-https://community-research-mcp.onrender.com/mcp}"
CLAUDE_DIR="${HOME}/Library/Application Support/Claude"
CONFIG_PATH="${CLAUDE_DIR}/claude_desktop_config.json"

mkdir -p "$CLAUDE_DIR"

if [[ ! -f "$CONFIG_PATH" ]]; then
  cat > "$CONFIG_PATH" <<'JSON'
{
  "mcpServers": {}
}
JSON
fi

BACKUP_PATH="${CONFIG_PATH}.backup.$(date +%Y%m%d-%H%M%S)"
cp "$CONFIG_PATH" "$BACKUP_PATH"

tmp_file="$(mktemp)"

python3 - "$CONFIG_PATH" "$tmp_file" "$SERVER_NAME" "$MCP_URL" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
server_name = sys.argv[3]
mcp_url = sys.argv[4]

try:
    data = json.loads(config_path.read_text(encoding="utf-8"))
except Exception:
    data = {}

if not isinstance(data, dict):
    data = {}

servers = data.get("mcpServers")
if not isinstance(servers, dict):
    servers = {}

servers[server_name] = {
    "command": "npx",
    "args": [
        "-y",
        "mcp-remote",
        mcp_url,
    ],
}

data["mcpServers"] = servers
out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

mv "$tmp_file" "$CONFIG_PATH"

echo "Claude Desktop MCP server updated: ${SERVER_NAME}"
echo "Config: ${CONFIG_PATH}"
echo "Backup: ${BACKUP_PATH}"
echo "Endpoint: ${MCP_URL}"
echo ""
echo "Next step: fully quit and reopen Claude Desktop."
