## ADDED Requirements

### Requirement: Single Environment Loading Entry Point
The system SHALL load file-based configuration through one function in the configuration layer, and that function SHALL run whenever `app.config` is imported. No other module SHALL call `load_dotenv` directly.

#### Scenario: MCP server picks up root .env
- **WHEN** `mcp_server.py` is started and the project `.env` defines `MCP_API_TIMEOUT_SECONDS`
- **THEN** the MCP server SHALL use the value from `.env`

#### Scenario: Script imports config without importing Reddit client
- **WHEN** a script imports only `app.config` and calls `get_runtime_config()`
- **THEN** the returned config SHALL reflect the values from the loaded env files

#### Scenario: No side-effect loading elsewhere
- **WHEN** the Python sources are searched for `load_dotenv` calls
- **THEN** the only call sites SHALL be in the configuration layer

### Requirement: Project Env File Resolution
The system SHALL resolve the project env file as the path in `ENV_FILE` when set, and otherwise as `<project root>/.env`, regardless of the process working directory.

#### Scenario: Started from a different working directory
- **WHEN** a process importing `app.config` is started with a working directory other than the project root
- **THEN** the system SHALL load `<project root>/.env`

#### Scenario: ENV_FILE override
- **WHEN** `ENV_FILE` points to an existing file containing `REDDIT_USER_AGENT=alt-agent`
- **THEN** `get_runtime_config().reddit_user_agent` SHALL equal `alt-agent`

#### Scenario: Explicit ENV_FILE missing
- **WHEN** `ENV_FILE` is set to a path that does not exist
- **THEN** startup SHALL fail with a configuration error naming the path and SHALL NOT print any secret values

#### Scenario: Default project file absent
- **WHEN** no `.env` exists at the project root and `ENV_FILE` is unset
- **THEN** startup SHALL continue without error

### Requirement: Shared Credentials File
The system SHALL additionally load a machine-wide env file from `SHARED_ENV_FILE` when that variable is set. Otherwise it SHALL load `$XDG_CONFIG_HOME/secrets/reddit.env`, falling back to `~/.config/secrets/reddit.env` when `XDG_CONFIG_HOME` is unset. The file SHALL use plain `KEY=value` dotenv syntax that a POSIX shell can `source`.

#### Scenario: Credentials only in shared file
- **WHEN** `REDDIT_CLIENT_ID` is absent from the process environment and the project file but present in the shared file
- **THEN** `get_runtime_config().reddit_client_id` SHALL equal the shared file value

#### Scenario: Explicit SHARED_ENV_FILE missing
- **WHEN** `SHARED_ENV_FILE` is set to a path that does not exist
- **THEN** startup SHALL fail with a configuration error naming the path

#### Scenario: Default shared file absent
- **WHEN** `SHARED_ENV_FILE` is unset and the default shared path does not exist
- **THEN** startup SHALL continue without error

#### Scenario: Loose permissions produce a warning
- **WHEN** the shared file is loaded and its mode grants any group or other permission bits
- **THEN** the system SHALL log a warning naming the path and recommending `chmod 600`, SHALL NOT include any values in the log, and SHALL still load the file

### Requirement: Environment Precedence
When the same variable is defined in more than one source, the value SHALL come from the highest-precedence source in this order: process environment, then the project env file, then the shared env file.

#### Scenario: Deployed variable wins over files
- **WHEN** `REDDIT_CLIENT_ID` is set in the process environment and in both env files
- **THEN** the process environment value SHALL be used

#### Scenario: Project file wins over shared file
- **WHEN** `REDDIT_USER_AGENT` is defined in both the project file and the shared file, and not in the process environment
- **THEN** the project file value SHALL be used

### Requirement: Credential Migration Helper
The repository SHALL provide a script that moves `REDDIT_*` entries from the project `.env` into the shared credentials file. The script SHALL be safe to run repeatedly and SHALL never print secret values.

#### Scenario: First run
- **WHEN** the script runs, the project `.env` contains `REDDIT_*` entries, and no shared file exists
- **THEN** it SHALL create the shared directory with mode `0700` and the shared file with mode `0600` containing those entries, back up the project `.env`, comment out the moved lines in the project `.env`, and print only key names

#### Scenario: Re-run is idempotent
- **WHEN** the script runs again after a successful first run
- **THEN** it SHALL NOT duplicate keys in the shared file or alter values already present there

### Requirement: Documented Variable Inventory
The repository SHALL track a `.env.example` in version control that lists every environment variable read by the Python services, including `ENV_FILE` and `SHARED_ENV_FILE`. It SHALL contain placeholder values only, grouped by the consuming service, and SHALL include a comment describing the shared file location and precedence.

#### Scenario: Example file is committed
- **WHEN** `git check-ignore .env.example` is run
- **THEN** the file SHALL NOT be ignored, while `.env` and other `.env.*` files SHALL remain ignored

#### Scenario: Inventory is complete
- **WHEN** every `os.getenv` name in `app/` and `mcp_server.py` is collected
- **THEN** every collected name SHALL appear in `.env.example`

#### Scenario: Example contains no real secrets
- **WHEN** `.env.example` is inspected
- **THEN** every credential variable SHALL contain only a placeholder value or be commented out
