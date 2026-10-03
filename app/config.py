import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECT_ENV_FILE = PROJECT_ROOT / ".env"


class ConfigurationError(ValueError):
    def __init__(self, missing_keys: list[str]):
        self.missing_keys = missing_keys
        keys = ", ".join(sorted(missing_keys))
        super().__init__(f"Missing required environment variables: {keys}")


class EnvFileNotFoundError(ConfigurationError):
    def __init__(self, variable: str, path: Path):
        self.missing_keys = [variable]
        self.path = path
        ValueError.__init__(self, f"{variable} points to a file that does not exist: {path}")


def default_shared_env_file() -> Path:
    config_home = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "secrets" / "reddit.env"


def _resolve_env_file(variable: str, default: Path) -> Path | None:
    explicit = os.getenv(variable)
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise EnvFileNotFoundError(variable, path)
        return path
    return default if default.is_file() else None


def _warn_if_shared_file_is_readable_by_others(path: Path) -> None:
    if path.stat().st_mode & 0o077:
        logger.warning(
            "Shared env file %s is accessible by other users; run: chmod 600 %s",
            path,
            path,
        )


def load_environment() -> list[Path]:
    """Load env files into os.environ without overriding variables already set.

    Precedence: process environment > project file (ENV_FILE or <project root>/.env)
    > shared file (SHARED_ENV_FILE or ~/.config/secrets/reddit.env).
    """
    loaded: list[Path] = []

    project_file = _resolve_env_file("ENV_FILE", DEFAULT_PROJECT_ENV_FILE)
    if project_file:
        load_dotenv(project_file, override=False)
        loaded.append(project_file)

    shared_file = _resolve_env_file("SHARED_ENV_FILE", default_shared_env_file())
    if shared_file:
        _warn_if_shared_file_is_readable_by_others(shared_file)
        load_dotenv(shared_file, override=False)
        loaded.append(shared_file)

    return loaded


load_environment()


@dataclass(frozen=True)
class RuntimeConfig:
    reddit_client_id: str | None
    reddit_client_secret: str | None
    reddit_user_agent: str
    reddit_username: str | None
    reddit_password: str | None
    mcp_port: int
    upstream_timeout_seconds: int
    retry_attempts: int
    retry_backoff_seconds: float
    max_comments: int
    min_search_limit: int
    max_search_limit: int
    replace_more_limit: int | None = 32


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a number") from exc


def _env_replace_more_limit(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    if raw.strip().lower() == "none":
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a non-negative integer or 'none'") from exc
    if value < 0:
        raise ValueError(f"Environment variable {name} must be a non-negative integer or 'none'")
    return value


@lru_cache(maxsize=1)
def get_runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "community_sentiment_app"),
        reddit_username=os.getenv("REDDIT_USERNAME"),
        reddit_password=os.getenv("REDDIT_PASSWORD"),
        mcp_port=_env_int("PORT", _env_int("MCP_PORT", 8000)),
        upstream_timeout_seconds=_env_int("REDDIT_TIMEOUT_SECONDS", 10),
        retry_attempts=max(1, _env_int("MCP_RETRY_ATTEMPTS", 3)),
        retry_backoff_seconds=max(0.1, _env_float("MCP_RETRY_BACKOFF_SECONDS", 0.5)),
        max_comments=max(1, _env_int("MCP_MAX_COMMENTS", 2000)),
        min_search_limit=1,
        max_search_limit=max(1, _env_int("MCP_MAX_SEARCH_LIMIT", 100)),
        replace_more_limit=_env_replace_more_limit("REDDIT_REPLACE_MORE_LIMIT", 32),
    )


def validate_runtime_config(config: RuntimeConfig) -> None:
    missing = []
    if not config.reddit_client_id:
        missing.append("REDDIT_CLIENT_ID")
    if not config.reddit_client_secret:
        missing.append("REDDIT_CLIENT_SECRET")
    if not config.reddit_user_agent:
        missing.append("REDDIT_USER_AGENT")

    if missing:
        raise ConfigurationError(missing)
