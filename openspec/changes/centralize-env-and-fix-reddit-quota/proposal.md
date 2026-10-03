## Why

Environment loading is an import side effect of `app/reddit.py`, so any entry point that doesn't import it (the MCP server, ad-hoc scripts, tests) silently ignores the root `.env`. `.env.example` is gitignored, so nobody cloning the repo can see what to configure. The Reddit credentials are also locked inside this repo's `.env`, so other projects on the same machine have to copy them.

The deployment config confuses Render service names with hostnames. Render keeps a service's original hostname when it is renamed, so in the dashboard (checked 2026-10-04 with `render services`) the two don't match:

- The API service is named `community-research-api` but is served at `community-research.onrender.com`.
- The frontend service is named `community-research` but is served at `community-research-frontend.onrender.com`.

As a result, `render.yaml` gives the frontend the wrong name (`community-research-frontend`). It also points the frontend's `NEXT_PUBLIC_API_URL` at `https://community-research-api.onrender.com`, a host with no service behind it (`x-render-routing: no-server`). A stale `.render.yaml` uses a third set of names.

Separately, the Reddit layer burns quota and mislabels failures:

- Missing threads and private subreddits are retried as "upstream unavailable".
- Every request builds a new PRAW client, which fetches a new OAuth token.
- `replace_more(limit=None)` expands entire threads even when only a few comments are requested.

## What Changes

- Add a single environment-loading entry point in the config layer. Every process (Flask API, MCP server, scripts, tests) gets it by importing `app.config`. Remove the side-effect `load_dotenv()` from `app/reddit.py`.
- Resolve the project `.env` from the project root rather than the working directory. Allow an `ENV_FILE` override.
- **Shared credentials file (option B).** Also load a machine-wide file, `~/.config/secrets/reddit.env` by default, overridable with `SHARED_ENV_FILE`. Other projects and tools can source the same file. Precedence is: process environment > project `.env` (or `ENV_FILE`) > shared file. If the shared file is readable by group or others, log a warning without printing any values.
- Add a helper script that moves the Reddit credential keys from the project `.env` into the shared file with `0600` permissions, and document how other projects consume it (shell `source`, Python `load_dotenv`, 1Password `op run`).
- Track `.env.example` in git and document every variable the Python services read.
- **Service URLs.**
  - Make `render.yaml` service names match the dashboard: keep `community-research-api` and `community-research-mcp`, and rename the frontend from `community-research-frontend` to `community-research`.
  - Point the MCP server and frontend at the API's real hostname, `https://community-research.onrender.com`.
  - Delete the stale `.render.yaml`.
  - Align `MCP_API_RETRY_ATTEMPTS` in `render.yaml` with the code default of 1.
  - Record the name-to-hostname mapping in one table, and add a test asserting that the `render.yaml` names match it and that every `*.onrender.com` hostname in the repo is one of its hostnames.
- The frontend reads the API URL at runtime from `COMMUNITY_RESEARCH_API_URL`, the same name the MCP server uses, instead of the build-time `NEXT_PUBLIC_API_URL`. The old name is kept as a fallback.
- Fix exception mapping so `NotFound` and `Forbidden` are no longer treated as retryable availability failures. Add the non-retryable error codes `NOT_FOUND` (404) and `FORBIDDEN` (403). This is an additive change to the response taxonomy.
- Reuse one PRAW client per service instance.
- Bound comment expansion with a configurable `REDDIT_REPLACE_MORE_LIMIT`, default 32.
- **BREAKING (behavioural)**: very large threads may no longer include every deeply collapsed comment by default. Setting `REDDIT_REPLACE_MORE_LIMIT=none` restores unbounded expansion.
- **BREAKING (deploy)**: the frontend's env var name changes. Before this fix, syncing the Blueprint would have created a second frontend service named `community-research-frontend`; after it, a sync matches all three existing services.
- The legacy `/search` CSV route chooses its HTTP status from structured error codes instead of substring-matching exception text.

## Capabilities

### New Capabilities
- `runtime-environment`: How every process discovers and loads configuration and credentials. Covers the project and shared env files, precedence, override paths, permission warnings, and the documented variable inventory.
- `service-endpoints`: Render service names (as shown in the dashboard) and their public hostnames, the single table that records the mapping, and the consistency check across the backend, MCP server, frontend, installer and Blueprint.
- `reddit-upstream-efficiency`: Not-found and forbidden classification, client reuse, and bounded comment expansion.

### Modified Capabilities
- None. The `mcp-reddit-server` capability from `extend-mcp-structured-reddit-v1` has not been archived into `openspec/specs/` yet.

## Impact

- **Python code:** `app/config.py`, `app/reddit.py`, `app/reddit_service.py`, `app/errors.py`, `app/routes.py`, `mcp_server.py`, and `tests/`.
- **Frontend:** `frontend/app/page.tsx`, which changes how the API URL is read.
- **Deployment:** `render.yaml` (frontend service rename, URLs, retry value) and the deletion of `.render.yaml`.
- **Tooling:** new `scripts/move-reddit-creds-to-shared.sh`.
- **Repo hygiene:** `.gitignore`, `.env.example`, and `README.md`.
- **API contract:** new error codes `NOT_FOUND` / `FORBIDDEN`.
- **Operations:** fewer Reddit API calls. Set `COMMUNITY_RESEARCH_API_URL` on the frontend service (dashboard name `community-research`), and check its current `NEXT_PUBLIC_API_URL`, which may point at the dead host.
- **Non-goals:**
  - OS keychain integration, beyond what `op run` provides through the process environment.
  - Render environment groups.
  - Custom domains.
  - Multi-threaded PRAW safety.
