from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def _secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("SECRET_KEY environment variable is not set.")
    return key


def _prepare(plain: str) -> bytes:
    # bcrypt has a 72-byte input limit; pre-hash with SHA-256 to support any password length
    return hashlib.sha256(plain.encode("utf-8")).digest()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_prepare(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        return None
