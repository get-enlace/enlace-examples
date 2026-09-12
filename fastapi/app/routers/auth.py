"""Authentication endpoints.

- POST /auth/register — create a new customer
- POST /oauth/token — RFC 6749 OAuth2 token endpoint (password + client_credentials grants)
  This endpoint is excluded from OpenAPI spec (include_in_schema=False) since it's not
  part of the API contract that Enlace's canvas directly calls — the credentials engine
  calls it directly.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    hash_password,
    mint_token,
    verify_password,
)
from ..config import settings
from ..db import get_db
from ..errors import bad_request, unauthorized
from ..models import Customer
from ..schemas import Customer as CustomerSchema
from ..schemas import ErrorResponse, LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=CustomerSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Email already registered"},
    },
)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> CustomerSchema:
    """Register a new customer.

    POST /auth/register
    body: { "name": string, "email": string, "password": string }
    -> 201 Customer
    """
    # Check if email already exists
    result = await db.execute(
        select(Customer).where(Customer.email == req.email)
    )
    existing = result.scalars().first()

    if existing:
        raise bad_request(f"Email {req.email} is already registered")

    # Create new customer
    password_hash = hash_password(req.password)
    customer = Customer(
        email=req.email,
        name=req.name,
        password_hash=password_hash,
    )
    db.add(customer)
    await db.flush()  # Get the ID without committing
    customer_id = customer.id

    return CustomerSchema(id=customer_id, email=req.email, name=req.name)


@router.post(
    "/oauth/token",
    response_model=TokenResponse,
    include_in_schema=False,  # Not in OpenAPI spec (Enlace's credential engine calls this)
    responses={
        400: {"model": ErrorResponse, "description": "Invalid grant or missing parameters"},
    },
)
async def token(
    grant_type: str = Form(...),
    username: str | None = Form(None),
    password: str | None = Form(None),
    client_id: str | None = Form(None),
    client_secret: str | None = Form(None),
    scope: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """RFC 6749 OAuth2 token endpoint — handles password and client_credentials grants.

    This endpoint is excluded from the OpenAPI spec because Enlace's own credential
    engine calls it directly (not a user-facing operation).

    **Password grant** (customer): username=email, password=password
    **Client credentials grant** (admin/service): client_id, client_secret
    (accepts either HTTP Basic auth or form fields; we support both)

    Response: { "access_token", "token_type": "Bearer", "expires_in": 3600, "scope": "..." }
    """
    if grant_type == "password":
        # Customer login: email + password -> customer token
        if not username or not password:
            raise bad_request("Missing username or password")

        result = await db.execute(
            select(Customer).where(Customer.email == username)
        )
        customer = result.scalars().first()

        if not customer or not verify_password(password, customer.password_hash):
            raise unauthorized("Invalid credentials")

        token = await mint_token(customer.id, "customer")
        return TokenResponse(
            access_token=token,
            token_type="Bearer",
            expires_in=settings.token_expiry_seconds,
            scope="customer",
        )

    elif grant_type == "client_credentials":
        # Admin/service login: client_id + client_secret -> admin token
        if not client_id or not client_secret:
            raise bad_request("Missing client_id or client_secret")

        if (
            client_id == settings.admin_client_id
            and client_secret == settings.admin_client_secret
        ):
            token = await mint_token(None, "admin")
            return TokenResponse(
                access_token=token,
                token_type="Bearer",
                expires_in=settings.token_expiry_seconds,
                scope="admin",
            )
        else:
            raise unauthorized("Invalid client credentials")

    else:
        raise bad_request(f"Unsupported grant_type: {grant_type}")
