from flask import Blueprint, render_template, request, Response, jsonify
import pandas as pd

from .errors import AppError, ErrorCode
from .mcp_response import error_response, internal_error_response, success_response
from .reddit import get_reddit_client
from .reddit_service import get_shared_reddit_service

main = Blueprint('main', __name__)


def _status_code_for_error(error: AppError) -> int:
    if error.code == ErrorCode.INVALID_INPUT:
        return 400
    if error.code == ErrorCode.AUTH_CONFIGURATION_ERROR:
        return 401
    if error.code == ErrorCode.UPSTREAM_RATE_LIMIT:
        return 429
    if error.code == ErrorCode.UPSTREAM_UNAVAILABLE:
        return 503
    return 500


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/about')
def about():
    return render_template('index.html')


@main.route('/redirect')
def redirect():
    return render_template('index.html')


@main.route('/health')
def health_check():
    """Health check endpoint to verify Reddit API connectivity."""
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
    subreddit = request.args.get("subreddit", "")
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
    except Exception as e:
        print(f"Error processing thread {thread_id}: {str(e)}")

        error_message = str(e).lower()
        if "invalid submission" in error_message or "submission does not exist" in error_message:
            return "Invalid Reddit thread ID. Please check the thread ID and try again.", 404
        if "unauthorized_client" in error_message:
            return "Reddit API authentication error. Please check your API credentials.", 401
        if "forbidden" in error_message or "access denied" in error_message:
            return "Access forbidden. The subreddit may be private or restricted.", 403
        if "not found" in error_message or "404" in error_message:
            return "Reddit thread not found. Please verify the thread ID.", 404
        if "rate limit" in error_message:
            return "Rate limit exceeded. Please try again later.", 429
        return f"Error processing Reddit thread: {str(e)}", 500
