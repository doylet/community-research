## ADDED Requirements

### Requirement: Single Name-to-Hostname Table
The repository SHALL record each Render service's dashboard name and public hostname in exactly one file, `deploy/services.yaml`. That file SHALL map `community-research-api` to `community-research.onrender.com`, `community-research` to `community-research-frontend.onrender.com`, and `community-research-mcp` to `community-research-mcp.onrender.com`.

#### Scenario: Table matches production
- **WHEN** `deploy/services.yaml` is parsed
- **THEN** it SHALL contain exactly those three name-to-hostname entries

### Requirement: Blueprint Names Match Dashboard Names
The service names in `render.yaml` SHALL be exactly the names in `deploy/services.yaml`. No other Render Blueprint file SHALL exist in the repository.

#### Scenario: Frontend uses its dashboard name
- **WHEN** `render.yaml` is parsed
- **THEN** the Node service with `rootDir: frontend` SHALL be named `community-research`

#### Scenario: API keeps its dashboard name
- **WHEN** `render.yaml` is parsed
- **THEN** the Python service started with `gunicorn main:app` SHALL be named `community-research-api`

#### Scenario: Name drift is caught
- **WHEN** a service in `render.yaml` has a name that is not a key in `deploy/services.yaml`
- **THEN** the endpoint consistency test SHALL fail and name the offending service

#### Scenario: Stale Blueprint removed
- **WHEN** the repository root is listed
- **THEN** `.render.yaml` SHALL NOT exist

### Requirement: Consistent API URL Wiring
Every consumer of the API base URL SHALL read it from `COMMUNITY_RESEARCH_API_URL`. In `render.yaml`, every consumer SHALL set it to the API's hostname from `deploy/services.yaml`, which is `https://community-research.onrender.com`.

#### Scenario: MCP server configured to live API
- **WHEN** `render.yaml` is parsed
- **THEN** the `community-research-mcp` service SHALL set `COMMUNITY_RESEARCH_API_URL` to `https://community-research.onrender.com`

#### Scenario: Frontend configured to live API
- **WHEN** `render.yaml` is parsed
- **THEN** the frontend service SHALL set `COMMUNITY_RESEARCH_API_URL` to `https://community-research.onrender.com` and SHALL NOT set `NEXT_PUBLIC_API_URL`

#### Scenario: Frontend reads URL at runtime
- **WHEN** the frontend server starts with `COMMUNITY_RESEARCH_API_URL` set and `NEXT_PUBLIC_API_URL` set to a different value
- **THEN** API requests SHALL go to the `COMMUNITY_RESEARCH_API_URL` value

#### Scenario: Frontend legacy variable fallback
- **WHEN** only `NEXT_PUBLIC_API_URL` is set
- **THEN** the frontend SHALL use its value

### Requirement: No References to Unknown Hosts
Every `*.onrender.com` hostname referenced in application code, the frontend, the installer script, the README, or `render.yaml` SHALL be a hostname listed in `deploy/services.yaml`.

#### Scenario: Name used as hostname is caught
- **WHEN** a tracked file references `https://community-research-api.onrender.com`
- **THEN** the endpoint consistency test SHALL fail and name the file and hostname, because that hostname is not in the table

#### Scenario: Current repository passes
- **WHEN** the endpoint consistency test runs after this change
- **THEN** it SHALL pass

### Requirement: Blueprint Retry Setting Matches Code Default
`render.yaml` SHALL NOT override `MCP_API_RETRY_ATTEMPTS` with a value different from the code default of 1.

#### Scenario: Retry attempts aligned
- **WHEN** `render.yaml` is parsed
- **THEN** `MCP_API_RETRY_ATTEMPTS` on `community-research-mcp` SHALL be absent or equal to `1`
