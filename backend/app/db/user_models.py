"""Per-user accounts and sessions.

Distinct from `security.py`'s API_ACCESS_TOKEN: that token gates the whole
API to keep outsiders out — it is one shared secret, not an identity, so an
audit-trail entry it authorizes can carry any auditor name a caller types in.
This adds a second, additive layer: a real account behind a login, so an
action that needs a genuine "who did this" — signing an audit entry — can be
attributed to a person instead of trusted on the caller's word.

Password storage uses PBKDF2-HMAC-SHA256 from the standard library rather
than adding a dependency (bcrypt/argon2) for a single-team internal tool.
600,000 iterations follows OWASP's current PBKDF2-SHA256 guidance.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String

from .database import Base


class UserORM(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)   # hex digest
    password_salt = Column(String, nullable=False)   # hex, unique per user
    role = Column(String, nullable=False, default="member")  # member | reviewer | admin
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False)


class UserSessionORM(Base):
    """One logged-in session. Deleting the row logs the session out —
    revocable in a way a self-contained signed token (JWT) is not, which
    matters more here than avoiding a DB lookup per request.
    """
    __tablename__ = "user_sessions"

    token = Column(String, primary_key=True)   # opaque, secrets.token_urlsafe
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
