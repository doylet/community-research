from flask import Blueprint, render_template, request, Response
from .reddit import get_reddit_client
import pandas as pd

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('index.html')

@main.route('/redirect')
def redirect():
    return render_template('index.html')

@main.route('/search')
def search_comments():
    thread_id = request.args.get("id")
    if not thread_id:
        return "Missing thread ID", 400
    
    reddit = get_reddit_client()
    submission = reddit.submission(id=thread_id)
    submission.comments.replace_more(limit=None)

    comments_data = []

        # Add thread metadata
    comments_data.append({
        "type": "post",
        "author": str(submission.author),
        "text": submission.title + "\n\n" + submission.selftext,
        "score": submission.score,
        "id": submission.id,
        "parent_id": None,
        "created_utc": submission.created_utc
    })

    # Add all top-level + nested comments
    for comment in submission.comments.list():
        comments_data.append({
            "type": "comment",
            "author": str(comment.author),
            "text": comment.body,
            "score": comment.score,
            "id": comment.id,
            "parent_id": comment.parent_id,
            "created_utc": comment.created_utc
        })

    df = pd.DataFrame(comments_data)

    # Return as downloadable CSV
    csv = df.to_csv(index=False)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=thread_{thread_id}.csv"}
    )
