"""Password hashing and session management. No FastAPI imports here, so it's easy to test."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import SESSION_LIFETIME_DAYS
from app.models import User, UserSession

_hasher = PasswordHasher()
# Used when the email doesn't exist, so a failed login takes the same time either way
# (otherwise response timing would reveal which emails are registered).
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalars(select(User).where(User.email == normalize_email(email))).first()
    try:
        _hasher.verify(user.password_hash if user else _DUMMY_HASH, password)
    except (VerifyMismatchError, InvalidHashError):
        return None
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    """Create a session and return the raw token (goes in the cookie, never stored)."""
    token = secrets.token_urlsafe(32)
    db.add(
        UserSession(
            token_hash=_hash_token(token),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=SESSION_LIFETIME_DAYS),
        )
    )
    db.commit()
    return token


def user_for_token(db: Session, token: str) -> User | None:
    session = db.get(UserSession, _hash_token(token))
    if session is None:
        return None
    if session.expires_at <= datetime.now(UTC):
        db.delete(session)
        db.commit()
        return None
    return session.user


def delete_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == _hash_token(token)))
    db.commit()
