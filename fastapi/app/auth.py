"""Authentication: password hashing, OAuth2 token generation/verification.

Implements /oauth/token (RFC 6749 password + client_credentials grants),
excluded from OpenAPI spec via include_in_schema=False.

Tokens are opaque strings, server-side cached (not JWTs), valid for
TOKEN_EXPIRY_SECONDS from minting. The token-endpoint response follows
RFC 6749 exactly (access_token, token_type, expires_in, scope).
"""

import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

from .config import settings
from .db import database

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


async def mint_token(customer_id: int | None, token_type: str) -> str:
    """Generate an opaque token and cache it server-side.

    Args:
        customer_id: the customer ID for 'customer' tokens, None for 'admin' tokens
        token_type: 'customer' or 'admin'

    Returns:
        opaque token string
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=settings.token_expiry_seconds)

    await database.execute(
        """INSERT INTO oauth_tokens (token, customer_id, token_type, expires_at)
           VALUES (:token, :customer_id, :token_type, :expires_at)""",
        values={
            "token": token,
            "customer_id": customer_id,
            "token_type": token_type,
            "expires_at": expires_at,
        },
    )

    return token


async def verify_token(token: str) -> dict | None:
    """Verify a token exists and hasn't expired. Returns token metadata or None.

    The metadata is used by dependency functions to identify the actor
    (customer_id for customer tokens, None for admin).
    """
    row = await database.fetch_one(
        """SELECT customer_id, token_type, expires_at FROM oauth_tokens
           WHERE token = :token AND expires_at > :now""",
        values={"token": token, "now": datetime.utcnow()},
    )
    if row:
        return dict(row)
    return None


async def verify_customer_bearer_token(token: str) -> int | None:
    """Verify a customer bearer token, return the customer_id.

    Used by routes that require customer auth (cart, order, etc).
    Returns customer_id if valid, None otherwise.
    """
    metadata = await verify_token(token)
    if metadata and metadata["token_type"] == "customer":
        return metadata["customer_id"]
    return None


async def verify_admin_bearer_token(token: str) -> bool:
    """Verify an admin bearer token.

    Used by routes that require admin auth (fulfill, product mgmt, etc).
    Returns True if valid, False otherwise.
    """
    metadata = await verify_token(token)
    return bool(metadata and metadata["token_type"] == "admin")


async def verify_carrier_api_key(api_key: str) -> bool:
    """Verify a carrier API key.

    Used by the shipment status endpoint (webhook from carrier).
    """
    return api_key == settings.carrier_api_key
