"""Per-user accounts, login, and session resolution.

See db/user_models.py for why this exists alongside the shared API token and
why sessions are DB-backed opaque tokens rather than JWTs.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ..db.database import SessionLocal
from ..db.user_models import UserORM, UserSessionORM

PBKDF2_ITERATIONS = 600_000
SESSION_LIFETIME_HOURS = 24 * 14  # 2 weeks
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """A user-facing auth failure — bad credentials, duplicate email, etc."""


@dataclass
class AuthenticatedUser:
    id: str
    email: str
    name: str
    role: str


def _hash_password(password: str, salt_hex: Optional[str] = None) -> tuple:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return digest.hex(), salt.hex()


def register_user(email: str, name: str, password: str) -> AuthenticatedUser:
    """Create an account. Open registration: the whole API already sits
    behind the shared access token, so this endpoint is not internet-facing
    on its own — it is a second, identity layer on top, not a replacement
    for the first gate.
    """
    email = email.strip().lower()
    name = name.strip()
    if not _EMAIL_RE.match(email):
        raise AuthError("That doesn't look like a valid email address.")
    if not name:
        raise AuthError("A name is required.")
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")

    session = SessionLocal()
    try:
        if session.query(UserORM).filter(UserORM.email == email).first():
            raise AuthError("An account with this email already exists.")
        password_hash, salt = _hash_password(password)
        user = UserORM(
            id=uuid.uuid4().hex,
            email=email,
            name=name,
            password_hash=password_hash,
            password_salt=salt,
            role="member",
            is_active=1,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        session.add(user)
        session.commit()
        return AuthenticatedUser(id=user.id, email=user.email, name=user.name, role=user.role)
    except AuthError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def login(email: str, password: str) -> tuple:
    """Verify credentials and open a new session. Returns (user, token).

    Failure paths (unknown email, wrong password, disabled account) all
    return the same generic error — distinguishing them would tell an
    attacker which emails have accounts.
    """
    email = email.strip().lower()
    session = SessionLocal()
    try:
        user = session.query(UserORM).filter(UserORM.email == email).first()
        if not user or not user.is_active:
            raise AuthError("Incorrect email or password.")
        candidate_hash, _ = _hash_password(password, user.password_salt)
        if not hmac.compare_digest(candidate_hash, user.password_hash):
            raise AuthError("Incorrect email or password.")

        token = secrets.token_urlsafe(32)
        now = datetime.now()
        session.add(UserSessionORM(
            token=token,
            user_id=user.id,
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=(now + timedelta(hours=SESSION_LIFETIME_HOURS)).strftime("%Y-%m-%d %H:%M:%S"),
        ))
        session.commit()
        return AuthenticatedUser(id=user.id, email=user.email, name=user.name, role=user.role), token
    finally:
        session.close()


def resolve_session(token: Optional[str]) -> Optional[AuthenticatedUser]:
    """The logged-in user for a session token, or None if absent/expired.

    None is a normal, expected result — most requests carry only the shared
    API token, not a personal session — so this never raises.
    """
    if not token:
        return None
    session = SessionLocal()
    try:
        record = session.get(UserSessionORM, token)
        if not record:
            return None
        if datetime.strptime(record.expires_at, "%Y-%m-%d %H:%M:%S") < datetime.now():
            session.delete(record)
            session.commit()
            return None
        user = session.get(UserORM, record.user_id)
        if not user or not user.is_active:
            return None
        return AuthenticatedUser(id=user.id, email=user.email, name=user.name, role=user.role)
    finally:
        session.close()


def logout(token: str) -> None:
    session = SessionLocal()
    try:
        record = session.get(UserSessionORM, token)
        if record:
            session.delete(record)
            session.commit()
    finally:
        session.close()
