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

from app.reddit import get_reddit_client

port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

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
) -> list[dict]:
    """Fetch the original post plus all comments from a Reddit thread.

    Returns a list of dicts with keys: type, author, text, score, id, parent_id, created_utc.
    """
    reddit = get_reddit_client()
    submission = reddit.submission(id=thread_id)
    submission.comments.replace_more(limit=None)

    results: list[dict] = []

    results.append({
        "type": "post",
        "author": str(submission.author),
        "text": submission.title + ("\n\n" + submission.selftext if submission.selftext else ""),
        "score": submission.score,
        "id": submission.id,
        "parent_id": None,
        "created_utc": submission.created_utc,
        "url": f"https://reddit.com{submission.permalink}",
    })

    for comment in submission.comments.list():
        results.append({
            "type": "comment",
            "author": str(comment.author),
            "text": comment.body,
            "score": comment.score,
            "id": comment.id,
            "parent_id": comment.parent_id,
            "created_utc": comment.created_utc,
            "url": f"https://reddit.com{comment.permalink}",
        })

    return results


@mcp.tool()
def search_subreddit(
    subreddit: Annotated[str, Field(description="Subreddit name without the r/ prefix, e.g. 'technology'")],
    query: Annotated[str, Field(description="Search query string")],
    limit: Annotated[int, Field(description="Maximum number of posts to return (1-100)", ge=1, le=100)] = 25,
    sort: Annotated[str, Field(description="Sort order: relevance, hot, top, new, comments")] = "relevance",
) -> list[dict]:
    """Search for posts in a subreddit matching a query.

    Returns a list of dicts with keys: id, title, author, score, url, num_comments, created_utc, selftext.
    """
    reddit = get_reddit_client()
    subreddit_obj = reddit.subreddit(subreddit)

    results: list[dict] = []
    for submission in subreddit_obj.search(query, sort=sort, limit=limit):
        results.append({
            "id": submission.id,
            "title": submission.title,
            "author": str(submission.author),
            "score": submission.score,
            "url": f"https://reddit.com{submission.permalink}",
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "selftext": submission.selftext[:500] if submission.selftext else "",
        })

    return results


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
