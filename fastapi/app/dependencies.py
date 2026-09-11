"""FastAPI security dependencies for OAuth2 and API key auth.

Uses FastAPI's native security classes so security schemes are auto-generated
in the OpenAPI spec. Enlace UI auto-discovers these and shows hints for
available credentials.
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, APIKeyHeader, HTTPAuthCredentials

from .auth import verify_admin_bearer_token, verify_carrier_api_key, verify_customer_bearer_token
from .errors import forbidden, unauthorized

# FastAPI security schemes (auto-added to OpenAPI spec)
http_bearer = HTTPBearer(
    description="Bearer token (OAuth2 password or client credentials grant)"
)
api_key = APIKeyHeader(
    name="X-Carrier-Api-Key",
    description="Carrier/third-party delivery partner API key",
)


async def get_current_customer_id(credentials: HTTPAuthCredentials = Depends(http_bearer)) -> int:
    """Verify customer bearer token from Authorization header.

    Raises 401 if missing or invalid, 403 if it's an admin token.

    FastAPI automatically adds this to the OpenAPI security schemes.
    """
    token = credentials.credentials
    customer_id = await verify_customer_bearer_token(token)
    if customer_id is None:
        raise unauthorized("Invalid or expired customer token")
    return customer_id


async def get_current_admin_id(credentials: HTTPAuthCredentials = Depends(http_bearer)) -> bool:
    """Verify admin bearer token from Authorization header.

    Raises 401 if missing or invalid, 403 if it's a customer token.

    FastAPI automatically adds this to the OpenAPI security schemes.
    """
    token = credentials.credentials
    is_admin = await verify_admin_bearer_token(token)
    if not is_admin:
        raise forbidden("Admin credentials required")
    return True


async def get_current_carrier_key(api_key_value: str = Depends(api_key)) -> str:
    """Verify carrier API key from X-Carrier-Api-Key header.

    Raises 401 if missing or invalid.

    FastAPI automatically adds this to the OpenAPI security schemes.
    """
    if not await verify_carrier_api_key(api_key_value):
        raise unauthorized("Invalid carrier API key")
    return api_key_value


async def get_customer_or_admin(credentials: HTTPAuthCredentials | None = Depends(http_bearer)) -> dict:
    """Extract customer OR admin from bearer token.

    Used by GET /orders which accepts either customer (scoped to own) or admin
    (scoped to all). Returns {"type": "customer", "id": <id>} or {"type": "admin"}.

    FastAPI automatically adds this to the OpenAPI security schemes.
    """
    if not credentials:
        raise unauthorized("Missing authorization header")

    token = credentials.credentials
    customer_id = await verify_customer_bearer_token(token)
    if customer_id is not None:
        return {"type": "customer", "id": customer_id}

    is_admin = await verify_admin_bearer_token(token)
    if is_admin:
        return {"type": "admin"}

    raise unauthorized("Invalid or expired token")
