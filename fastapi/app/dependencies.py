"""FastAPI security dependencies for OAuth2 and API key auth.

Uses FastAPI's native security classes so security schemes are auto-generated
in the OpenAPI spec. Enlace UI auto-discovers these and shows hints for
available credentials.
"""

from fastapi import Depends, Header
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from .auth import verify_admin_bearer_token, verify_carrier_api_key, verify_customer_bearer_token
from .errors import forbidden, unauthorized

# FastAPI security schemes (auto-added to OpenAPI spec with distinct identities)
# These are declared separately so Enlace can distinguish between them

customer_oauth = HTTPBearer(
    scheme_name="Customer JWT",
    description="Customer login (OAuth2 password grant)",
)

admin_oauth = HTTPBearer(
    scheme_name="Admin JWT",
    description="Admin/service credentials (OAuth2 client credentials grant)",
)

carrier_api_key = APIKeyHeader(
    name="X-Carrier-Api-Key",
    description="Carrier/third-party delivery partner API key",
)


async def get_current_customer_id(credentials: HTTPAuthorizationCredentials = Depends(customer_oauth)) -> int:
    """Verify customer bearer token from Authorization header.

    Raises 401 if missing or invalid, 403 if it's an admin token.

    FastAPI automatically adds this as a distinct credential in the OpenAPI spec.
    HTTPBearer returns HTTPAuthorizationCredentials with a .credentials attribute.
    """
    customer_id = await verify_customer_bearer_token(credentials.credentials)
    if customer_id is None:
        raise unauthorized("Invalid or expired customer token")
    return customer_id


async def get_current_admin_id(credentials: HTTPAuthorizationCredentials = Depends(admin_oauth)) -> bool:
    """Verify admin bearer token from Authorization header.

    Raises 401 if missing or invalid, 403 if it's a customer token.

    FastAPI automatically adds this as a distinct credential in the OpenAPI spec.
    HTTPBearer returns HTTPAuthorizationCredentials with a .credentials attribute.
    """
    is_admin = await verify_admin_bearer_token(credentials.credentials)
    if not is_admin:
        raise forbidden("Admin credentials required")
    return True


async def get_current_carrier_key(api_key_value: str = Depends(carrier_api_key)) -> str:
    """Verify carrier API key from X-Carrier-Api-Key header.

    Raises 401 if missing or invalid.

    FastAPI automatically adds this to the OpenAPI security schemes.
    """
    if not await verify_carrier_api_key(api_key_value):
        raise unauthorized("Invalid carrier API key")
    return api_key_value


async def get_customer_or_admin(authorization: str | None = Header(None)) -> dict:
    """Extract customer OR admin from bearer token.

    Used by GET /orders which accepts either customer (scoped to own) or admin
    (scoped to all). Returns {"type": "customer", "id": <id>} or {"type": "admin"}.

    This endpoint accepts either credential, so it uses manual header extraction.
    """
    # Extract from Authorization header manually for this dual-auth endpoint
    if not authorization:
        raise unauthorized("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise unauthorized("Invalid authorization header format")

    token = authorization[len("Bearer "):]
    customer_id = await verify_customer_bearer_token(token)
    if customer_id is not None:
        return {"type": "customer", "id": customer_id}

    is_admin = await verify_admin_bearer_token(token)
    if is_admin:
        return {"type": "admin"}

    raise unauthorized("Invalid or expired token")
