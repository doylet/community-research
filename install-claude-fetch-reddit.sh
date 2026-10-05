#!/usr/bin/env bash
set -euo pipefail

SERVER_NAME="fetch-reddit"
MCP_URL="${1:-https://community-research-mcp.onrender.com/mcp}"
MCP_REMOTE_VERSION="${MCP_REMOTE_VERSION:-0.1.38}"
MCP_REMOTE_PACKAGE="${MCP_REMOTE_PACKAGE:-mcp-remote@${MCP_REMOTE_VERSION}}"
CLAUDE_DIR="${HOME}/Library/Application Support/Claude"
CONFIG_PATH="${CLAUDE_DIR}/claude_desktop_config.json"

add_node_candidate() {
    local candidate="$1"
    local existing

    [[ -x "$candidate" ]] || return

    for existing in "${NODE_CANDIDATES[@]:-}"; do
        [[ "$existing" == "$candidate" ]] && return
    done

    NODE_CANDIDATES+=("$candidate")
}

NODE_CANDIDATES=()

if command -v node >/dev/null 2>&1; then
    add_node_candidate "$(command -v node)"
fi

add_node_candidate "/opt/homebrew/bin/node"
add_node_candidate "/usr/local/bin/node"

NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -d "$NVM_DIR/versions/node" ]]; then
    shopt -s nullglob
    for node_path in "$NVM_DIR"/versions/node/*/bin/node; do
        add_node_candidate "$node_path"
    done
    shopt -u nullglob
fi

BEST_NODE=""
BEST_NODE_MAJOR=0

for node_bin in "${NODE_CANDIDATES[@]:-}"; do
    node_major="$($node_bin -p 'process.versions.node.split(".")[0]' 2>/dev/null || true)"
    if [[ "$node_major" =~ ^[0-9]+$ ]] && (( node_major >= 22 )) && (( node_major > BEST_NODE_MAJOR )); then
        BEST_NODE="$node_bin"
        BEST_NODE_MAJOR=$node_major
    fi
done

NPX_CMD="${BEST_NODE%/node}/npx"

if [[ -z "$BEST_NODE" || ! -x "$NPX_CMD" ]]; then
    echo "Error: npx not found. Install Node.js 22+ and rerun." >&2
    exit 1
fi

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

python3 - "$CONFIG_PATH" "$tmp_file" "$SERVER_NAME" "$MCP_URL" "$NPX_CMD" "$MCP_REMOTE_PACKAGE" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
server_name = sys.argv[3]
mcp_url = sys.argv[4]
npx_cmd = sys.argv[5]
mcp_remote_package = sys.argv[6]

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
    "command": npx_cmd,
    "args": [
        "-y",
        mcp_remote_package,
        mcp_url,
        "--transport",
        "http-only",
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
echo "npx: ${NPX_CMD}"
echo "mcp-remote: ${MCP_REMOTE_PACKAGE}"
echo ""
echo "Next step: fully quit and reopen Claude Desktop."
