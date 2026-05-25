"""
MongoDB helpers — save summaries to the 'summaries' collection.
"""

import os
from datetime import datetime, timezone

from pymongo import MongoClient

_client = None


def _get_collection():
    """Connect once and return the summaries collection."""
    global _client
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise ValueError("MONGO_URI is not set in environment variables")

    if _client is None:
        _client = MongoClient(uri)
        # Database name comes from the URI path (e.g. .../ai_summarizer)
        db = _client.get_default_database()
        if db is None:
            raise ValueError(
                "Add a database name to MONGO_URI, e.g. "
                "mongodb+srv://...@cluster.mongodb.net/ai_summarizer"
            )

    return _client.get_default_database()["summaries"]


def save_summary(
    original_text: str,
    url: str,
    summary: str,
    length: str,
) -> None:
    """Insert one summary document."""
    doc = {
        "original_text": original_text,
        "url": url or "",
        "summary": summary,
        "length": length,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _get_collection().insert_one(doc)
