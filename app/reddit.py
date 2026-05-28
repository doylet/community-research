from dotenv import load_dotenv
import praw

from .config import RuntimeConfig, get_runtime_config

load_dotenv()


def get_reddit_client(config: RuntimeConfig | None = None):
    runtime_config = config or get_runtime_config()
    return praw.Reddit(
        client_id=runtime_config.reddit_client_id,
        client_secret=runtime_config.reddit_client_secret,
        user_agent=runtime_config.reddit_user_agent,
        username=runtime_config.reddit_username,
        password=runtime_config.reddit_password,
        timeout=runtime_config.upstream_timeout_seconds,
    )