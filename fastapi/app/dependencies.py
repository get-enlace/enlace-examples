"""FastAPI dependency functions for extracting auth from request headers.

Used via @router.get(..., dependencies=[Depends(require_customer)]) or
async def my_route(customer_id: int = Depends(get_current_customer_id), ...):
"""

from fastapi import Depends, Header

from .auth import verify_admin_bearer_token, verify_carrier_api_key, verify_customer_bearer_token
from .errors import forbidden, unauthorized


async def get_current_customer_id(authorization: str | None = Header(None)) -> int:
    """Extract customer ID from Bearer token in Authorization header.

    Raises 401 if missing or invalid, 403 if it's an admin token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized("Missing or invalid authorization header")

    token = authorization[len("Bearer ") :]
    customer_id = await verify_customer_bearer_token(token)
    if customer_id is None:
        raise unauthorized("Invalid or expired token")
    return customer_id


async def get_current_admin_id(authorization: str | None = Header(None)) -> bool:
    """Verify admin Bearer token in Authorization header.

    Raises 401 if missing or invalid, 403 if it's a customer token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized("Missing or invalid authorization header")

    token = authorization[len("Bearer ") :]
    is_admin = await verify_admin_bearer_token(token)
    if not is_admin:
        raise forbidden("Admin credentials required")
    return True


async def get_current_carrier_key(x_carrier_api_key: str | None = Header(None)) -> str:
    """Extract carrier API key from X-Carrier-Api-Key header.

    Raises 401 if missing or invalid.
    """
    if not x_carrier_api_key or not await verify_carrier_api_key(x_carrier_api_key):
        raise unauthorized("Invalid carrier API key")
    return x_carrier_api_key


async def get_customer_or_admin(
    authorization: str | None = Header(None),
) -> dict:
    """Extract customer OR admin from Bearer token.

    Used by GET /orders which accepts either customer (scoped to own) or admin
    (scoped to all). Returns {"type": "customer", "id": <id>} or {"type": "admin"}.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized("Missing or invalid authorization header")

    token = authorization[len("Bearer ") :]
    customer_id = await verify_customer_bearer_token(token)
    if customer_id is not None:
        return {"type": "customer", "id": customer_id}

    is_admin = await verify_admin_bearer_token(token)
    if is_admin:
        return {"type": "admin"}

    raise unauthorized("Invalid or expired token")
