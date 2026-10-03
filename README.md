# Community Research

Backend service for Reddit community data retrieval with both Flask routes and an MCP server endpoint.

The MCP process calls the API service over HTTP. Reddit credentials are only needed by the API service.

## Local Setup

Python is pinned in `.python-version` (3.11); Render reads the same file. Dependencies are fully locked (exact versions).

```bash
uv venv                                          # creates .venv using .python-version
uv pip sync requirements.txt requirements-dev.txt
source .venv/bin/activate
cp .env.example .env                             # then fill in Reddit credentials
```

Without uv: `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`.

### Changing dependencies

Edit `requirements.in` (runtime) or `requirements-dev.in` (tests/tooling), never the `.txt` lock files directly, then regenerate and commit both:

```bash
uv pip compile requirements.in -o requirements.txt --python-version 3.11
uv pip compile requirements-dev.in -o requirements-dev.txt --python-version 3.11
uv pip sync requirements.txt requirements-dev.txt
```

Add `--upgrade-package <name>` to bump a single package; existing pins are otherwise preserved.

## Environment Variables

Every variable is listed in `.env.example`. Any process that imports `app.config` (the API, the MCP server, tests, scripts) loads configuration in this order, and the first source that defines a key wins:

1. **Process environment**: Render, CI, `op run`, your shell. These are never overwritten.
2. **Project env file**: `ENV_FILE` if set, otherwise `<project root>/.env`. The path is fixed to the repo, so it works from any working directory.
3. **Shared credentials file**: `SHARED_ENV_FILE` if set, otherwise `~/.config/secrets/reddit.env` (or `$XDG_CONFIG_HOME/secrets/reddit.env`).

If you set `ENV_FILE` or `SHARED_ENV_FILE` and the file doesn't exist, startup fails. If a default file is missing, it is skipped. If the shared file is readable by other users, a warning is logged; no values are printed.

Required (API service):
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT

Optional:
- REDDIT_USERNAME
- REDDIT_PASSWORD
- PORT or MCP_PORT (default: 8000)
- REDDIT_TIMEOUT_SECONDS (default: 10)
- REDDIT_REPLACE_MORE_LIMIT (default: 32): the maximum number of "load more comments" requests per thread fetch. Set it to `none` for unlimited, which uses much more API quota on large threads. When enough comments are already loaded, no expansion requests are made.
- MCP_RETRY_ATTEMPTS (default: 3)
- MCP_RETRY_BACKOFF_SECONDS (default: 0.5)
- MCP_MAX_COMMENTS (default: 2000)
- MCP_MAX_SEARCH_LIMIT (default: 100)
- COMMUNITY_RESEARCH_FRONTEND_URL: where `/` and `/about` redirect to

MCP-specific:
- COMMUNITY_RESEARCH_API_URL (required for MCP process)
- MCP_API_TIMEOUT_SECONDS (default: REDDIT_TIMEOUT_SECONDS)
- MCP_API_RETRY_ATTEMPTS (default: 1)
- MCP_API_RETRY_BACKOFF_SECONDS (default: MCP_RETRY_BACKOFF_SECONDS)

Frontend: `COMMUNITY_RESEARCH_API_URL`, read on the server when each request is handled, so changing it only needs a restart. `NEXT_PUBLIC_API_URL` is still accepted as a fallback.

Startup validates required Reddit credentials in the API service.

### Sharing Reddit credentials with other projects

Keep the Reddit credentials in the shared file, and keep only project-specific settings in `.env`. To move the `REDDIT_*` lines out of this project's `.env`, run:

```bash
scripts/move-reddit-creds-to-shared.sh
```

The script:

- Creates `~/.config/secrets/` (mode 700) and the shared file (mode 600).
- Copies each value exactly as written.
- Backs up `.env` to `.env.bak.<timestamp>` and comments out the moved lines.
- Prints key names only, never values.
- Is safe to re-run. If the shared file already has a *different* value for a key, the project line is left in place.

Other projects can then read the same file:

```bash
# shell / Makefile
set -a; source ~/.config/secrets/reddit.env; set +a

# direnv (.envrc)
dotenv ~/.config/secrets/reddit.env

# 1Password: keep op:// references in the file and inject at runtime
op run --env-file ~/.config/secrets/reddit.env -- python app.py
```

```python
# Python
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.home() / ".config/secrets/reddit.env")
```

## Deploying (Render)

`render.yaml` is the Blueprint. Render keeps a service's original hostname when it is renamed, so **dashboard names and hostnames don't match**:

| Dashboard name | Hostname |
|---|---|
| `community-research-api` | `community-research.onrender.com` (API) |
| `community-research` | `community-research-frontend.onrender.com` (frontend) |
| `community-research-mcp` | `community-research-mcp.onrender.com` (MCP) |

The mapping is defined in `deploy/services.yaml`:

- `render.yaml` must use the dashboard names, because Blueprints match services by name.
- Code and docs must use the hostnames.
- `tests/test_service_endpoints.py` enforces both.
- If you rename a service in the dashboard, update `deploy/services.yaml` first.

One manual step is needed when moving the frontend to the new variable. On the `community-research` (frontend) service:

1. Set `COMMUNITY_RESEARCH_API_URL=https://community-research.onrender.com`.
2. Once that deploy is live, remove `NEXT_PUBLIC_API_URL`.

## Health Endpoints

- `/health`: lightweight API process health (no Reddit API call)
- `/health/reddit`: explicit Reddit connectivity diagnostics (calls Reddit API)

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
    "fetch-reddit": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://community-research-mcp.onrender.com/mcp"
      ]
    }
  }
}

Install helper script (macOS):

./install-claude-fetch-reddit.sh

Optional custom MCP URL:

./install-claude-fetch-reddit.sh https://community-research-mcp.onrender.com/mcp

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
- NOT_FOUND (thread or subreddit does not exist; HTTP 404, not retried)
- FORBIDDEN (private, quarantined or banned; HTTP 403, not retried)
- AUTH_CONFIGURATION_ERROR
- UPSTREAM_RATE_LIMIT
- UPSTREAM_UNAVAILABLE
- INTERNAL_ERROR

## Tests

python -m pytest
