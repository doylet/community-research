import os
from dataclasses import dataclass
from functools import lru_cache


class ConfigurationError(ValueError):
    def __init__(self, missing_keys: list[str]):
        self.missing_keys = missing_keys
        keys = ", ".join(sorted(missing_keys))
        super().__init__(f"Missing required environment variables: {keys}")


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
