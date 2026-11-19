from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth import service
from app.auth.deps import CurrentUser, DbSession
from app.config import SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE, SESSION_LIFETIME_DAYS
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)  # no min length: don't reveal rules on login


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_LIFETIME_DAYS * 24 * 60 * 60,
        httponly=True,  # not readable from JavaScript
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",  # not sent on cross-site form posts (CSRF protection)
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: Credentials, db: DbSession, response: Response) -> UserOut:
    email = service.normalize_email(body.email)
    if db.scalars(select(User).where(User.email == email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(email=email, password_hash=service.hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous sign-ups with the same email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    _set_session_cookie(response, service.create_session(db, user))
    return UserOut.model_validate(user)


@router.post("/login")
def login(body: LoginCredentials, db: DbSession, response: Response) -> UserOut:
    user = service.authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    _set_session_cookie(response, service.create_session(db, user))
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: DbSession,
    response: Response,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> None:
    if session_token:
        service.delete_session(db, session_token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
