from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.errors import DuplicateKeyError

from api.models.auth import Token, UserCreate, UserLogin, UserOut
from api.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.mongodb import create_user, get_mongo_db, get_user_by_email, get_user_by_id

router = APIRouter()
_bearer = HTTPBearer()

_DB_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Database not available. Set MONGO_URI in .env and restart the API.",
)


def _user_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        username=doc["username"],
        created_at=doc["created_at"],
    )


def _get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    user = get_user_by_id(payload.get("sub", ""))
    if user is None or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate):
    if get_mongo_db() is None:
        raise _DB_UNAVAILABLE
    if get_user_by_email(body.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    try:
        doc = create_user(
            email=body.email,
            username=body.username,
            hashed_password=hash_password(body.password),
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken.")
    return _user_out(doc)


@router.post("/login", response_model=Token)
def login(body: UserLogin):
    if get_mongo_db() is None:
        raise _DB_UNAVAILABLE
    user = get_user_by_email(body.email)
    hashed = user.get("hashed_password") if user else None
    if not hashed or not verify_password(body.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    token = create_access_token({"sub": str(user["_id"])})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(_get_current_user)):
    return _user_out(current_user)
