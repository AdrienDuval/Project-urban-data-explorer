"""Quick script to inspect and optionally clear the users collection.

Run with:  python scripts/inspect_users.py
Add --clear to wipe the collection for a fresh start.
"""
import sys
from pathlib import Path

# Load .env so MONGO_URI is available
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.mongodb import get_mongo_db, USERS_COLL

db = get_mongo_db()
if db is None:
    print("ERROR: MONGO_URI not set — check .env")
    sys.exit(1)

users = list(db[USERS_COLL].find({}, {"hashed_password": 0}))
print(f"\n=== users collection ({len(users)} documents) ===")
for u in users:
    print(f"  _id={u['_id']}  username={u.get('username')}  email={u.get('email')}  created={u.get('created_at')}")

if "--clear" in sys.argv:
    result = db[USERS_COLL].delete_many({})
    print(f"\n✓ Deleted {result.deleted_count} user(s). Collection is now empty.")
else:
    print("\nRun with --clear to wipe all users for a fresh start.")
