"""
HTTP MCP server exposing Reddit research tools.

Run locally:
    python mcp_server.py

The server starts on http://0.0.0.0:8000/mcp (streamable-http transport).

Tools exposed:
  - fetch_thread_comments   Return all comments from a Reddit thread.
  - search_subreddit        Search posts in a subreddit.
"""

import os
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from app.config import ConfigurationError, get_runtime_config, validate_runtime_config
from app.errors import AppError
from app.mcp_response import error_response, internal_error_response, success_response
from app.reddit_service import get_shared_reddit_service

runtime_config = get_runtime_config()
port = int(os.getenv("PORT", os.getenv("MCP_PORT", str(runtime_config.mcp_port))))

mcp = FastMCP(
    name="community-research",
    instructions=(
        "Tools for fetching Reddit community data. "
        "Use fetch_thread_comments to retrieve all comments from a specific thread. "
        "Use search_subreddit to find relevant posts in a community."
    ),
    host="0.0.0.0",
    port=port,
    streamable_http_path="/mcp",
)


@mcp.tool()
def fetch_thread_comments(
    thread_id: Annotated[str, Field(description="Reddit submission ID (the alphanumeric part of the post URL, e.g. 'abc123')")],
    max_comments: Annotated[int, Field(description="Maximum number of comments to include", ge=1)] = runtime_config.max_comments,
) -> dict:
    """Fetch the original post plus all comments from a Reddit thread.

    Returns a list of dicts with keys: type, author, text, score, id, parent_id, created_utc.
    """
    try:
        result = get_shared_reddit_service().fetch_thread_records(
            thread_id=thread_id,
            max_comments=max_comments,
            include_url=True,
        )
        return success_response(result.data, retries=result.retries)
    except AppError as exc:
        return error_response(exc)
    except Exception:
        return internal_error_response()


@mcp.tool()
def search_subreddit(
    subreddit: Annotated[str, Field(description="Subreddit name without the r/ prefix, e.g. 'technology'")],
    query: Annotated[str, Field(description="Search query string")],
    limit: Annotated[int, Field(description="Maximum number of posts to return (1-100)", ge=1, le=100)] = 25,
    sort: Annotated[str, Field(description="Sort order: relevance, hot, top, new, comments")] = "relevance",
) -> dict:
    """Search for posts in a subreddit matching a query.

    Returns a list of dicts with keys: id, title, author, score, url, num_comments, created_utc, selftext.
    """
    try:
        result = get_shared_reddit_service().search_posts(
            subreddit=subreddit,
            query=query,
            limit=limit,
            sort=sort,
        )
        return success_response(result.data, retries=result.retries)
    except AppError as exc:
        return error_response(exc)
    except Exception:
        return internal_error_response()


if __name__ == "__main__":
    try:
        validate_runtime_config(runtime_config)
    except ConfigurationError as exc:
        raise SystemExit(f"Startup configuration error: {exc}") from exc

    mcp.run(transport="streamable-http")
