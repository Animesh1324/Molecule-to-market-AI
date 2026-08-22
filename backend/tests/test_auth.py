"""Per-user accounts: registration, login, sessions, and the identity
guarantee they exist to provide — an audit entry's `auditor` field must
reflect who is actually logged in, never what a caller types.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.services import auth_service as auth

init_db()
client = TestClient(app)


def _fresh_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


# --------------------------------------------------------------------------
# Service layer
# --------------------------------------------------------------------------

def test_register_and_login_round_trip():
    email = _fresh_email()
    registered = auth.register_user(email, "Test User", "correcthorse123")
    assert registered.email == email

    user, token = auth.login(email, "correcthorse123")
    assert user.id == registered.id
    assert len(token) > 20


def test_login_rejects_wrong_password():
    email = _fresh_email()
    auth.register_user(email, "Test User", "correcthorse123")
    with pytest.raises(auth.AuthError):
        auth.login(email, "wrongpassword")


def test_login_rejects_unknown_email():
    with pytest.raises(auth.AuthError):
        auth.login(_fresh_email(), "whatever123")


def test_register_rejects_duplicate_email():
    email = _fresh_email()
    auth.register_user(email, "First", "correcthorse123")
    with pytest.raises(auth.AuthError):
        auth.register_user(email, "Second", "differentpass123")


def test_register_rejects_short_password():
    with pytest.raises(auth.AuthError):
        auth.register_user(_fresh_email(), "Test", "short")


def test_register_rejects_invalid_email():
    with pytest.raises(auth.AuthError):
        auth.register_user("not-an-email", "Test", "correcthorse123")


def test_password_is_never_stored_in_plain_text():
    email = _fresh_email()
    auth.register_user(email, "Test User", "correcthorse123")
    from app.db.database import SessionLocal
    from app.db.user_models import UserORM
    session = SessionLocal()
    try:
        row = session.query(UserORM).filter(UserORM.email == email).first()
        assert row.password_hash != "correcthorse123"
        assert "correcthorse123" not in row.password_hash
    finally:
        session.close()


def test_resolve_session_returns_none_for_garbage_token():
    assert auth.resolve_session("not-a-real-token") is None


def test_resolve_session_returns_none_after_logout():
    email = _fresh_email()
    auth.register_user(email, "Test User", "correcthorse123")
    _, token = auth.login(email, "correcthorse123")
    assert auth.resolve_session(token) is not None
    auth.logout(token)
    assert auth.resolve_session(token) is None


def test_expired_session_is_treated_as_logged_out():
    from datetime import datetime, timedelta
    from app.db.database import SessionLocal
    from app.db.user_models import UserSessionORM

    email = _fresh_email()
    user = auth.register_user(email, "Test User", "correcthorse123")
    session = SessionLocal()
    try:
        expired_token = "expired-test-token-" + uuid.uuid4().hex
        session.add(UserSessionORM(
            token=expired_token, user_id=user.id,
            created_at=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        ))
        session.commit()
    finally:
        session.close()
    assert auth.resolve_session(expired_token) is None


# --------------------------------------------------------------------------
# API layer
# --------------------------------------------------------------------------

def test_register_endpoint():
    response = client.post("/api/auth/register", json={
        "email": _fresh_email(), "name": "API Test", "password": "correcthorse123"})
    assert response.status_code == 200
    assert response.json()["name"] == "API Test"


def test_register_endpoint_rejects_short_password():
    response = client.post("/api/auth/register", json={
        "email": _fresh_email(), "name": "API Test", "password": "short"})
    assert response.status_code == 422


def test_login_endpoint_round_trip():
    email = _fresh_email()
    client.post("/api/auth/register", json={"email": email, "name": "API Test", "password": "correcthorse123"})
    response = client.post("/api/auth/login", json={"email": email, "password": "correcthorse123"})
    assert response.status_code == 200
    assert "session_token" in response.json()


def test_login_endpoint_rejects_bad_password():
    email = _fresh_email()
    client.post("/api/auth/register", json={"email": email, "name": "API Test", "password": "correcthorse123"})
    response = client.post("/api/auth/login", json={"email": email, "password": "wrongpassword"})
    assert response.status_code == 401


def test_me_endpoint_requires_a_session():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_endpoint_returns_the_logged_in_user():
    email = _fresh_email()
    client.post("/api/auth/register", json={"email": email, "name": "API Test", "password": "correcthorse123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "correcthorse123"})
    token = login.json()["session_token"]
    response = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_logout_invalidates_the_session():
    email = _fresh_email()
    client.post("/api/auth/register", json={"email": email, "name": "API Test", "password": "correcthorse123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "correcthorse123"})
    token = login.json()["session_token"]
    client.post("/api/auth/logout", headers={"X-Session-Token": token})
    response = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert response.status_code == 401
