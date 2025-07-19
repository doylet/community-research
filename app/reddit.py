# app/reddit_client.py
import os
from dotenv import load_dotenv
import praw

load_dotenv()


def get_reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "community_sentiment_app")
    )