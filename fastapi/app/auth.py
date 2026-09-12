"""Authentication: password hashing, OAuth2 token generation/verification."""

import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

from .config import settings
from .db import get_session_factory
from .models import OAuthToken

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        ph.verify(password_hash, password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False


def mint_token(customer_id: int | None, token_type: str) -> str:
    """Generate an opaque token and cache it server-side."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=settings.token_expiry_seconds)

    session_local = get_session_factory()
    db = session_local()
    try:
        oauth_token = OAuthToken(
            token=token,
            customer_id=customer_id,
            token_type=token_type,
            expires_at=expires_at,
        )
        db.add(oauth_token)
        db.commit()
    finally:
        db.close()

    return token


def verify_token(token: str) -> dict | None:
    """Verify a token exists and hasn't expired."""
    session_local = get_session_factory()
    db = session_local()
    try:
        row = db.query(OAuthToken).filter(
            (OAuthToken.token == token)
            & (OAuthToken.expires_at > datetime.utcnow())
        ).first()

        if row:
            return {
                "customer_id": row.customer_id,
                "token_type": row.token_type,
                "expires_at": row.expires_at,
            }
        return None
    finally:
        db.close()


def verify_customer_bearer_token(token: str) -> int | None:
    """Verify a customer bearer token, return the customer_id."""
    metadata = verify_token(token)
    if metadata and metadata["token_type"] == "customer":
        return metadata["customer_id"]
    return None


def verify_admin_bearer_token(token: str) -> bool:
    """Verify an admin bearer token."""
    metadata = verify_token(token)
    return bool(metadata and metadata["token_type"] == "admin")


def verify_carrier_api_key(api_key: str) -> bool:
    """Verify a carrier API key."""
    return api_key == settings.carrier_api_key
