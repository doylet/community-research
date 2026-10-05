import logging
import os

from flask import Blueprint, request, Response, jsonify, redirect as flask_redirect
import pandas as pd

from .errors import AppError, ErrorCode
from .mcp_response import error_response, internal_error_response, success_response
from .reddit import get_reddit_client
from .reddit_service import get_shared_reddit_service

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("COMMUNITY_RESEARCH_FRONTEND_URL", "https://community-research-frontend.onrender.com").rstrip("/")


def _frontend_redirect(path: str = "/"):
    target = f"{FRONTEND_URL}{path}"
    return flask_redirect(target, code=302)


def _status_code_for_error(error: AppError) -> int:
    if error.code == ErrorCode.INVALID_INPUT:
        return 400
    if error.code == ErrorCode.NOT_FOUND:
        return 404
    if error.code == ErrorCode.FORBIDDEN:
        return 403
    if error.code == ErrorCode.AUTH_CONFIGURATION_ERROR:
        return 401
    if error.code == ErrorCode.UPSTREAM_RATE_LIMIT:
        return 429
    if error.code == ErrorCode.UPSTREAM_UNAVAILABLE:
        return 503
    return 500


@main.route('/')
def index():
    return _frontend_redirect("/")


@main.route('/about')
def about():
    return _frontend_redirect("/about")


@main.route('/redirect')
def redirect_to_frontend():
    return _frontend_redirect("/")


@main.route('/health')
def health_check():
    """Lightweight process health check that does not call upstream services."""
    return jsonify({
        "status": "healthy",
        "service": "community-research-api",
    })


@main.route('/health/reddit')
def health_check_reddit():
    """Diagnostic health endpoint to verify Reddit API connectivity."""
    try:
        reddit = get_reddit_client()
        test_sub = reddit.subreddit('test')
        test_sub.display_name
        return jsonify({
            "status": "healthy",
            "reddit_api": "connected",
            "read_only": reddit.read_only,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "reddit_api": "disconnected",
            "error": str(e),
        }), 500


@main.route('/test')
def test_reddit():
    """Test endpoint to verify Reddit API is working with a known thread."""
    try:
        reddit = get_reddit_client()
        test_submission = reddit.submission(id="16k5n6l")
        return jsonify({
            "status": "success",
            "title": test_submission.title,
            "author": str(test_submission.author) if test_submission.author else "[deleted]",
            "score": test_submission.score,
            "read_only": reddit.read_only,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }), 500


@main.route('/api/thread')
def api_thread_records():
    thread_id = request.args.get("thread_id") or request.args.get("id")
    if not thread_id:
        return jsonify(error_response(AppError(ErrorCode.INVALID_INPUT, "Missing thread_id"))), 400

    max_comments_raw = request.args.get("max_comments")
    max_comments = None
    if max_comments_raw is not None:
        try:
            max_comments = int(max_comments_raw)
        except ValueError:
            return jsonify(error_response(AppError(ErrorCode.INVALID_INPUT, "max_comments must be an integer"))), 400

    include_url = request.args.get("include_url", "1").strip().lower() not in {"0", "false", "no"}

    try:
        result = get_shared_reddit_service().fetch_thread_records(
            thread_id=thread_id,
            max_comments=max_comments,
            include_url=include_url,
        )
        return jsonify(success_response(result.data, retries=result.retries))
    except AppError as exc:
        return jsonify(error_response(exc)), _status_code_for_error(exc)
    except Exception:
        return jsonify(internal_error_response()), 500


@main.route('/api/search_posts')
def api_search_posts():
    subreddit = (request.args.get("subreddit") or "all").strip() or "all"
    query = request.args.get("query", "")
    sort = request.args.get("sort", "relevance")

    limit_raw = request.args.get("limit", "25")
    try:
        limit = int(limit_raw)
    except ValueError:
        return jsonify(error_response(AppError(ErrorCode.INVALID_INPUT, "limit must be an integer"))), 400

    try:
        result = get_shared_reddit_service().search_posts(
            subreddit=subreddit,
            query=query,
            limit=limit,
            sort=sort,
        )
        return jsonify(success_response(result.data, retries=result.retries))
    except AppError as exc:
        return jsonify(error_response(exc)), _status_code_for_error(exc)
    except Exception:
        return jsonify(internal_error_response()), 500


CSV_ERROR_MESSAGES = {
    ErrorCode.INVALID_INPUT: "Invalid Reddit thread ID. Please check the thread ID and try again.",
    ErrorCode.NOT_FOUND: "Reddit thread not found. Please verify the thread ID.",
    ErrorCode.FORBIDDEN: "Access forbidden. The subreddit may be private or restricted.",
    ErrorCode.AUTH_CONFIGURATION_ERROR: "Reddit API authentication error. Please check your API credentials.",
    ErrorCode.UPSTREAM_RATE_LIMIT: "Rate limit exceeded. Please try again later.",
    ErrorCode.UPSTREAM_UNAVAILABLE: "Reddit is temporarily unavailable. Please try again later.",
}


@main.route('/search')
def search_comments():
    thread_id = request.args.get("id")
    if not thread_id:
        return "Missing thread ID", 400

    try:
        result = get_shared_reddit_service().fetch_thread_records(
            thread_id=thread_id,
            include_url=False,
        )
        comments_data = result.data

        # Preserve legacy CSV column order for downstream compatibility.
        columns = ["type", "author", "text", "score", "id", "parent_id", "created_utc"]
        df = pd.DataFrame(comments_data, columns=columns)

        csv = df.to_csv(index=False)
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=thread_{thread_id}.csv"},
        )
    except AppError as exc:
        message = CSV_ERROR_MESSAGES.get(exc.code, "Error processing Reddit thread. Please try again later.")
        return message, _status_code_for_error(exc)
    except Exception:
        logger.exception("Unexpected error exporting thread %s", thread_id)
        return "Error processing Reddit thread. Please try again later.", 500
