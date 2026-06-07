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
import time
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field
import requests

from app.config import get_runtime_config
from app.errors import AppError, ErrorCode
from app.mcp_response import error_response, internal_error_response, success_response

runtime_config = get_runtime_config()
port = int(os.getenv("PORT", os.getenv("MCP_PORT", str(runtime_config.mcp_port))))
api_base_url = os.getenv("COMMUNITY_RESEARCH_API_URL", "https://community-research.onrender.com").rstrip("/")
api_timeout_seconds = int(os.getenv("MCP_API_TIMEOUT_SECONDS", str(runtime_config.upstream_timeout_seconds)))
api_retry_attempts = max(1, int(os.getenv("MCP_API_RETRY_ATTEMPTS", "1")))
api_retry_backoff_seconds = float(os.getenv("MCP_API_RETRY_BACKOFF_SECONDS", str(runtime_config.retry_backoff_seconds)))

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


def _status_error(status_code: int) -> AppError:
    if status_code == 400:
        return AppError(ErrorCode.INVALID_INPUT, "Invalid request parameters")
    if status_code == 401:
        return AppError(ErrorCode.AUTH_CONFIGURATION_ERROR, "Upstream service authentication is invalid")
    if status_code == 429:
        return AppError(ErrorCode.UPSTREAM_RATE_LIMIT, "Upstream service rate limit exceeded", retryable=True)
    if status_code >= 500:
        return AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "Upstream service is temporarily unavailable", retryable=True)
    return AppError(ErrorCode.INTERNAL_ERROR, "Unexpected response from upstream service")


def _extract_upstream_error(payload: dict, status_code: int) -> AppError:
    error_block = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error_block, dict):
        code = error_block.get("code")
        message = error_block.get("message")
        if isinstance(code, str) and isinstance(message, str):
            retryable = code in {ErrorCode.UPSTREAM_RATE_LIMIT, ErrorCode.UPSTREAM_UNAVAILABLE}
            return AppError(code=code, message=message, retryable=retryable)
    return _status_error(status_code)


def _call_service(path: str, params: dict) -> tuple[list[dict], int]:
    transport_retries = 0

    for attempt in range(1, api_retry_attempts + 1):
        try:
            response = requests.get(
                f"{api_base_url}{path}",
                params=params,
                timeout=api_timeout_seconds,
            )
        except requests.RequestException:
            if attempt >= api_retry_attempts:
                raise AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "Failed to reach upstream service", retryable=True)
            transport_retries += 1
            time.sleep(api_retry_backoff_seconds * (2 ** (attempt - 1)))
            continue

        try:
            payload = response.json()
        except ValueError:
            if response.status_code >= 500 and attempt < api_retry_attempts:
                transport_retries += 1
                time.sleep(api_retry_backoff_seconds * (2 ** (attempt - 1)))
                continue
            raise _status_error(response.status_code)

        if response.status_code >= 500 and attempt < api_retry_attempts:
            transport_retries += 1
            time.sleep(api_retry_backoff_seconds * (2 ** (attempt - 1)))
            continue

        if response.status_code >= 400:
            raise _extract_upstream_error(payload, response.status_code)

        if not isinstance(payload, dict):
            raise AppError(ErrorCode.INTERNAL_ERROR, "Invalid upstream response envelope")

        if payload.get("success") is not True:
            raise _extract_upstream_error(payload, response.status_code)

        data = payload.get("data")
        if not isinstance(data, list):
            raise AppError(ErrorCode.INTERNAL_ERROR, "Upstream response missing list data")

        upstream_retries = 0
        meta = payload.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get("retries"), int):
            upstream_retries = meta["retries"]

        return data, transport_retries + upstream_retries

    raise AppError(ErrorCode.INTERNAL_ERROR, "Retry loop exited unexpectedly")


def _validate_api_service_configuration() -> None:
    if not api_base_url:
        raise SystemExit("Startup configuration error: COMMUNITY_RESEARCH_API_URL is required")

    try:
        probe_response = requests.get(
            f"{api_base_url}/api/thread",
            timeout=api_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise SystemExit(f"Startup dependency error: API service is unreachable at {api_base_url}: {exc}") from exc

    if probe_response.status_code >= 500:
        raise SystemExit(
            f"Startup dependency error: API service returned HTTP {probe_response.status_code} at {api_base_url}"
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
        data, retries = _call_service(
            "/api/thread",
            {
                "thread_id": thread_id,
                "max_comments": max_comments,
                "include_url": 1,
            },
        )
        return success_response(data, retries=retries)
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
        data, retries = _call_service(
            "/api/search_posts",
            {
                "subreddit": subreddit,
                "query": query,
                "limit": limit,
                "sort": sort,
            },
        )
        return success_response(data, retries=retries)
    except AppError as exc:
        return error_response(exc)
    except Exception:
        return internal_error_response()


if __name__ == "__main__":
    _validate_api_service_configuration()
    mcp.run(transport="streamable-http")
