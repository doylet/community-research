from flask import Blueprint, render_template, request, Response
from .reddit_service import get_shared_reddit_service
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

    result = get_shared_reddit_service().fetch_thread_records(
        thread_id=thread_id,
        include_url=False,
    )
    comments_data = result.data

    # Preserve legacy CSV column order for downstream compatibility.
    columns = ["type", "author", "text", "score", "id", "parent_id", "created_utc"]
    df = pd.DataFrame(comments_data, columns=columns)

    # Return as downloadable CSV
    csv = df.to_csv(index=False)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=thread_{thread_id}.csv"}
    )
