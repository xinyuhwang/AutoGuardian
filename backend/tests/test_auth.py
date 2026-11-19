from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import SESSION_COOKIE_NAME
from app.models import User, UserSession

PASSWORD = "correct horse battery"


def register(client: TestClient, email: str = "owner@example.com", password: str = PASSWORD):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_logs_in_and_hashes_password(client: TestClient, db: Session) -> None:
    response = register(client, email="Owner@Example.com ")
    assert response.status_code == 201
    assert response.json()["email"] == "owner@example.com"  # normalized
    assert client.get("/auth/me").json()["email"] == "owner@example.com"

    user = db.scalars(select(User)).one()
    assert user.password_hash != PASSWORD and user.password_hash.startswith("$argon2")


def test_session_cookie_is_http_only(client: TestClient) -> None:
    response = register(client)
    cookie = response.headers["set-cookie"].lower()
    assert SESSION_COOKIE_NAME in cookie and "httponly" in cookie and "samesite=lax" in cookie


def test_session_token_is_stored_hashed(client: TestClient, db: Session) -> None:
    register(client)
    token = client.cookies[SESSION_COOKIE_NAME]
    stored = db.scalars(select(UserSession)).one()
    assert stored.token_hash != token and len(stored.token_hash) == 64


def test_duplicate_email_rejected(client: TestClient) -> None:
    register(client)
    assert register(client, email="OWNER@example.com").status_code == 409


def test_short_password_rejected(client: TestClient) -> None:
    assert register(client, password="short").status_code == 422


def test_login_logout_flow(client: TestClient) -> None:
    register(client)
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401

    response = client.post("/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert response.status_code == 200
    assert client.get("/auth/me").status_code == 200


def test_login_wrong_password_and_unknown_email_look_the_same(client: TestClient) -> None:
    register(client)
    client.post("/auth/logout")
    wrong = client.post("/auth/login", json={"email": "owner@example.com", "password": "nope-nope"})
    unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_logout_invalidates_old_token(client: TestClient) -> None:
    register(client)
    token = client.cookies[SESSION_COOKIE_NAME]
    client.post("/auth/logout")
    client.cookies.set(SESSION_COOKIE_NAME, token)  # replay the old cookie
    assert client.get("/auth/me").status_code == 401


def test_expired_session_rejected(client: TestClient, db: Session) -> None:
    register(client)
    session = db.scalars(select(UserSession)).one()
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert client.get("/auth/me").status_code == 401


def test_endpoints_require_login(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    assert client.get("/vehicles").status_code == 401
    assert client.post("/vehicles", json={"year": 2018, "make": "Honda", "model": "Accord"}).status_code == 401
