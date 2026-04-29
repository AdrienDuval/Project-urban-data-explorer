"""MongoDB helpers for Urban Data Explorer (NoSQL analytics).

Set ``MONGO_URI`` in the environment (e.g. ``.env`` at project root). If unset,
analytics calls return unavailable status from the API without crashing imports.

Collections:

- ``zone_user_interests``: one document per (anonymous ``user_key``, ``zone_id``)
  with incremental ``clicks`` — answers “which zones does this visitor care about”.
- Aggregated interest per zone is computed via aggregation (total clicks per zone).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Load .env from project root (parent of ``src/``)
_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")

DB_NAME = "Urban_data_explorer"
ZONE_INTERESTS_COLL = "zone_user_interests"
USERS_COLL = "users"

_client: MongoClient | None = None
_indexes_ensured = False
_user_indexes_ensured = False


def _mongo_uri() -> str | None:
    uri = os.environ.get("MONGO_URI", "").strip()
    return uri or None


def get_mongo_client() -> MongoClient | None:
    """Return a singleton client, or ``None`` if ``MONGO_URI`` is not configured."""
    global _client
    if _mongo_uri() is None:
        return None
    if _client is None:
        _client = MongoClient(_mongo_uri(), serverSelectionTimeoutMS=8000)
    return _client


def get_mongo_db() -> Database | None:
    client = get_mongo_client()
    return client[DB_NAME] if client else None


def _ensure_indexes(collection: Collection) -> None:
    global _indexes_ensured
    if _indexes_ensured:
        return
    collection.create_index(
        [("user_key", ASCENDING), ("zone_id", ASCENDING)],
        unique=True,
        name="user_zone_unique",
    )
    collection.create_index([("zone_id", ASCENDING)], name="zone_lookup")
    _indexes_ensured = True


def record_zone_click(
    *,
    user_key: str,
    zone_id: str,
    zone_name: str | None = None,
    geography: str | None = None,
) -> bool:
    """Increment click count for ``user_key`` × ``zone_id``. Returns ``True`` if Mongo accepted the write."""
    db = get_mongo_db()
    if db is None:
        return False
    coll = db[ZONE_INTERESTS_COLL]
    _ensure_indexes(coll)
    now = datetime.now(timezone.utc)
    coll.update_one(
        {"user_key": user_key, "zone_id": zone_id},
        {
            "$inc": {"clicks": 1},
            "$set": {
                "updated_at": now,
                "zone_name": zone_name,
                "geography": geography,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    return True


def aggregate_zone_totals(*, limit: int = 50) -> list[dict[str, Any]]:
    """Total clicks per zone across all users (popularity ranking)."""
    db = get_mongo_db()
    if db is None:
        return []
    coll = db[ZONE_INTERESTS_COLL]
    cursor = coll.aggregate(
        [
            {
                "$group": {
                    "_id": "$zone_id",
                    "total_clicks": {"$sum": "$clicks"},
                    "zone_name": {"$first": "$zone_name"},
                    "geography": {"$first": "$geography"},
                }
            },
            {"$sort": {"total_clicks": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "zone_id": "$_id",
                    "total_clicks": 1,
                    "zone_name": 1,
                    "geography": 1,
                }
            },
        ]
    )
    return list(cursor)


def user_zone_interests(*, user_key: str, limit: int = 50) -> list[dict[str, Any]]:
    """Zones this anonymous user clicked most (interest profile)."""
    db = get_mongo_db()
    if db is None:
        return []
    coll = db[ZONE_INTERESTS_COLL]
    cursor = (
        coll.find({"user_key": user_key}, projection={"_id": 0})
        .sort([("clicks", -1)])
        .limit(limit)
    )
    return list(cursor)


def _ensure_user_indexes(collection: Collection) -> None:
    global _user_indexes_ensured
    if _user_indexes_ensured:
        return
    collection.create_index([("email", ASCENDING)], unique=True, name="email_unique")
    collection.create_index([("username", ASCENDING)], unique=True, name="username_unique")
    _user_indexes_ensured = True


def create_user(
    *,
    email: str,
    username: str,
    hashed_password: str,
) -> dict[str, Any]:
    """Insert a new user document. Raises ``DuplicateKeyError`` if email/username taken."""
    db = get_mongo_db()
    if db is None:
        raise RuntimeError("MongoDB is not configured (MONGO_URI not set).")
    coll = db[USERS_COLL]
    _ensure_user_indexes(coll)
    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {
        "email": email.lower().strip(),
        "username": username.strip(),
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Return user document by email, or ``None`` if not found."""
    db = get_mongo_db()
    if db is None:
        return None
    return db[USERS_COLL].find_one({"email": email.lower().strip()})


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Return user document by string ``_id``, or ``None`` if not found."""
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return db[USERS_COLL].find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


if __name__ == "__main__":
    # Smoke test: ``python -m src.mongodb`` with ``MONGO_URI`` set
    db = get_mongo_db()
    if db is None:
        print("MONGO_URI not set — skipping.")
    else:
        print(f"Connected to {DB_NAME}, collections sample OK.")
        print("zone totals:", aggregate_zone_totals(limit=5))
