## Context

**Entry points.** The repo runs three Python entry points: the Flask API (`main.py` → `app/`), the MCP server (`mcp_server.py`, which proxies to the API over HTTP), and tests and scripts. A Next.js frontend in `frontend/` renders on the server and calls the API.

**How config loads today.** Configuration is read in `app/config.py` via `os.getenv`, behind a cached `get_runtime_config()`. `.env` is only loaded by a module-level `load_dotenv()` in `app/reddit.py`, which the MCP server never imports.

**Credentials across projects.** The Reddit credentials live only in this repo's `.env`, so other projects or tools that want them must copy them.

**Live deployment** (verified 2026-10-04 with `render services` and Render routing headers):

| Dashboard name | Public hostname | Role | Created |
|---|---|---|---|
| `community-research-api` | `community-research.onrender.com` | API (gunicorn) | 2025-07-19 |
| `community-research` | `community-research-frontend.onrender.com` | Frontend (`rootDir: frontend`) | 2026-05-31 |
| `community-research-mcp` | `community-research-mcp.onrender.com` | MCP (uvicorn) | 2026-04-23 |

The names and hostnames don't line up because Render keeps a service's original hostname when it is renamed. The API was created as `community-research` and later renamed, which freed that name for the frontend. Blueprints match services by **name**, but code needs **hostnames**, and the repo currently conflates the two:

- `render.yaml` names the frontend `community-research-frontend`, its hostname, rather than its dashboard name `community-research`. Syncing would create a duplicate frontend.
- `render.yaml` sets the frontend's `NEXT_PUBLIC_API_URL` to `community-research-api.onrender.com`, the API's name used as a hostname. That host has no service (`x-render-routing: no-server`).
- `.render.yaml` is an older Blueprint with a third set of names. Render only reads `render.yaml`.

The frontend's current env vars in the dashboard haven't been checked. Hardcoded `*.onrender.com` URLs also appear in `app/routes.py`, `mcp_server.py`, `install-claude-fetch-reddit.sh`, `README.md`, and three frontend files.

**Reddit layer bugs.** In prawcore, `NotFound` and `Forbidden` subclass `ResponseException`, which is checked first, so both are classified as retryable `UPSTREAM_UNAVAILABLE`. A new `praw.Reddit` client is also built on every operation.

## Goals / Non-Goals

**Goals:**
- Every Python process loads env files the same way, just by importing `app.config`.
- One machine-wide credentials file that this project and others can share, with per-project overrides.
- `render.yaml` matches production, and nothing in the repo references a hostname it doesn't declare.
- The API URL has one variable name across the MCP server and frontend, and is read at runtime.
- Correct not-found and forbidden handling, fewer Reddit API calls, and one OAuth token per process.

**Non-Goals:**
- OS Keychain integration. 1Password users can use `op run`, which injects into the process environment, so no code is needed.
- Render env groups, custom domains, and preview environments.
- Making PRAW safe for multi-threaded workers.

## Decisions

### D1: Load env at import time in `app/config.py`
`load_environment()` is defined in `app/config.py` and called once at import. `app/reddit.py` drops its `load_dotenv()`. Import time is the earliest hook that every entry point already passes through. Exposing it as a function lets tests re-run it with temporary files and then call `get_runtime_config.cache_clear()`.

- *Rejected:* a `load_dotenv()` call in each entry point, because it is easy to forget and causes the current bug.
- *Rejected:* `pydantic-settings`, which would mean rewriting `RuntimeConfig` for little gain.

### D2: Layered files, real environment wins
Files load in this order, all with `override=False`, so the first source to define a key wins:

1. **Process environment.** It is never overwritten, which protects values on Render, in CI and from `op run`.
2. **Project file.** This is `ENV_FILE` if set, otherwise `<project root>/.env`, resolved as `Path(__file__).resolve().parent.parent / ".env"`.
3. **Shared file.** This is `SHARED_ENV_FILE` if set, otherwise `$XDG_CONFIG_HOME/secrets/reddit.env`, falling back to `~/.config/secrets/reddit.env`.

Error handling depends on whether a path was set explicitly. If `ENV_FILE` or `SHARED_ENV_FILE` is set but the file is missing, raise `ConfigurationError` naming the path, because an explicit path that doesn't exist is a mistake. If a default path is missing, skip it silently, because that is the normal case on Render.

*Why the project file outranks the shared file:* a project can pin a different Reddit app or user agent without editing the shared file. The usual setup is credentials in the shared file and project-specific settings in `.env`.

### D3: The shared file is plain dotenv, not a new format
The shared file uses `KEY=value` lines that `source`, `python-dotenv`, `direnv` (`dotenv ~/.config/secrets/reddit.env`) and `op run --env-file` all understand. Other projects need no library from this repo.

*Rejected:* macOS Keychain via `keyring`. It adds a dependency, doesn't work on Render or Linux, and isn't readable from a shell.

*Rejected:* a JSON or TOML secrets file, because it can't be sourced from a shell.

### D4: Permission warning, not refusal
When the shared file is loaded and its mode has any group or other bits set (`mode & 0o077`), log a warning that names the path and suggests `chmod 600`. Values are never logged. Refusing to load would break first-time setup, so the warning is enough.

### D5: Migration helper script
`scripts/move-reddit-creds-to-shared.sh` works as follows:

1. Create `~/.config/secrets/` with mode `0700`.
2. Copy the `REDDIT_*` lines from the project `.env` into the shared file, without overwriting keys that already exist there.
3. `chmod 600` the shared file.
4. Comment out the moved lines in the project `.env`, after making a timestamped backup.
5. Print key names only, never values.

The script is idempotent. It is a separate script rather than automatic behaviour, because moving secrets should always be a deliberate action.

### D6: `render.yaml` names match the dashboard; hostnames are recorded separately
- Keep `community-research-api` and `community-research-mcp` as they are, and rename the frontend to `community-research`, so that all three names match the dashboard and a Blueprint sync updates the existing services instead of creating new ones.
- Do not rename the dashboard services to make the names and hostnames agree. A rename doesn't change the hostname, so it would fix nothing and risk confusion.
- Set `COMMUNITY_RESEARCH_API_URL` for the MCP server and the frontend to `https://community-research.onrender.com`.
- Set `COMMUNITY_RESEARCH_FRONTEND_URL` on the API service, which `routes.py` already reads.
- Delete `.render.yaml`.
- Set `MCP_API_RETRY_ATTEMPTS` to `1`, matching the code default from commit `be12952`. The current value of 3 silently undoes that commit.

Code fallbacks (`mcp_server.py`, `routes.py`, the frontend and the installer) keep their production defaults, so local runs and the Claude Desktop installer work without extra config. A test keeps them consistent with the Blueprint, as described in D8.

*Rejected:* `fromService` references in the Blueprint. Render's `host` property returns the internal private-network hostname, not the public `onrender.com` URL, and free-plan services can't use private networking. Explicit public URLs are simpler.

### D7: Frontend reads the API URL at runtime under the shared name
`page.tsx` is a server component, so it can read `process.env.COMMUNITY_RESEARCH_API_URL` at request time. `NEXT_PUBLIC_*` values, by contrast, are inlined at build time. The lookup order is `COMMUNITY_RESEARCH_API_URL`, then `NEXT_PUBLIC_API_URL` for compatibility, then the production default. Changing the URL then only needs a restart, not a rebuild. The footer and navigation links use the same constant.

### D8: One name-to-hostname table, and a test that enforces it
Hostnames can't be derived from service names, so the mapping is recorded once in `deploy/services.yaml`:

```yaml
community-research-api: community-research.onrender.com
community-research: community-research-frontend.onrender.com
community-research-mcp: community-research-mcp.onrender.com
```

The README's Deploying section refers to this file instead of repeating the table. `tests/test_service_endpoints.py` loads it and `render.yaml` with PyYAML (a dev-only dependency), and checks the following:

- The service names in `render.yaml` are exactly the keys of `deploy/services.yaml`.
- Every `*.onrender.com` hostname in the tracked files is one of the table's values. The files checked are `app/`, `mcp_server.py`, `frontend/app`, `frontend/components`, `frontend/lib`, `install-claude-fetch-reddit.sh`, `README.md` and `render.yaml`.
- Every URL-valued env var in `render.yaml` also uses one of the table's hostnames.
- `.render.yaml` does not exist.

*Rejected:* an optional live check against `render services -o json`. It needs CLI authentication and network access in CI. It can be added later as a manual script.

PyYAML is not a transitive dependency, so it is added to `requirements-dev.in` and the dev lock is regenerated with uv. It is a test-only dependency and stays out of the runtime lock.

### D9: New error codes, checked before `ResponseException`
The mapping order is `TooManyRequests` → `NotFound` (`NOT_FOUND`, 404) → `Forbidden` (`FORBIDDEN`, 403) → `OAuthException` (`AUTH_CONFIGURATION_ERROR`) → the generic `RequestException`/`ResponseException`/`ServerError` (retryable `UPSTREAM_UNAVAILABLE`).

The MCP server's `_extract_upstream_error` already passes code strings through. `_status_error` gains 403 and 404 branches for responses with no JSON body.

### D10: Lazily cached client
`RedditService._client()` builds the client on its first call and stores it in `self._reddit`. Because the service is a per-process singleton, this means one client and one OAuth token per process. This is safe under gunicorn's single-threaded sync workers.

### D11: Two-stage bounded comment expansion
1. Count the comments already loaded, excluding `MoreComments`.
2. If the count is at least `comment_limit`, call `replace_more(limit=0)`, which makes no network calls.
3. Otherwise call `replace_more(limit=config.replace_more_limit)`. The default is 32, matching PRAW's own default, and the value `none` means unlimited.

*Rejected:* deriving the limit from `max_comments`, because the number of comments each expansion returns varies too much to predict.

### D12: Structured errors in the `/search` CSV route
Catch `AppError` and use `_status_code_for_error` with a fixed message for each code. For any other exception, log it on the server and return a generic 500 that doesn't echo the error.

## Risks / Trade-offs

- [Risk] A future rename in the dashboard silently breaks the name match again, and the next Blueprint sync creates a duplicate service. → Mitigation: `deploy/services.yaml` and the README note that a dashboard rename must be mirrored there, and the endpoint test makes `render.yaml` follow it.
- [Risk] The deployed frontend may currently have `NEXT_PUBLIC_API_URL=https://community-research-api.onrender.com`, in which case the dashboard search is broken today. → Mitigation: setting `COMMUNITY_RESEARCH_API_URL` on the frontend service fixes it without a rebuild, because it takes priority over `NEXT_PUBLIC_API_URL`.
- [Risk] Credentials in a file outside the repo are easy to forget when setting up a new machine. → Mitigation: `.env.example` and the README document the shared file path and the helper script.
- [Risk] A shared file is a wider blast radius, since every project using it holds the same Reddit app secret. → Mitigation: keep the permission warning and use read-only credentials. Projects that need isolation can set their own values in their project `.env`, which takes priority.
- [Risk] A developer's own `.env` or shared file could leak into tests. → Mitigation: an autouse fixture in `tests/conftest.py` points both `ENV_FILE` and `SHARED_ENV_FILE` at empty temporary files and clears the config cache.
- [Risk] Large-thread exports will contain fewer comments. → Mitigation: document `REDDIT_REPLACE_MORE_LIMIT=none`.
- [Trade-off] Un-ignoring `.env.example` risks committing secrets. → Mitigation: a test asserts that `.env.example` contains only placeholders.

## Migration Plan

1. Merge the change. The Python services need no environment changes on Render.
2. On the frontend service (dashboard name `community-research`), set `COMMUNITY_RESEARCH_API_URL=https://community-research.onrender.com`, then remove `NEXT_PUBLIC_API_URL` once the new frontend is deployed. After that, all three Blueprint names match the dashboard, so a sync updates the existing services.
3. On each development machine, run `scripts/move-reddit-creds-to-shared.sh` (optional). Other projects can then use `~/.config/secrets/reddit.env`.
4. Rollback: revert the commit. The shared file is harmless if left in place, because the project `.env` backup restores the previous local setup.

## Open Questions

- ~~What is the frontend service's current `NEXT_PUBLIC_API_URL`?~~ Resolved on 2026-10-04: it is `https://community-research.onrender.com`, which is correct. The service was created manually, not from `render.yaml`, so production was never broken. Setting `COMMUNITY_RESEARCH_API_URL` and removing `NEXT_PUBLIC_API_URL` are both safe in either order and need no deploy coordination, because the running build already has the URL inlined and every fallback resolves to the same host.
