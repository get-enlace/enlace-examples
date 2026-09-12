"""Authentication endpoints - synchronous."""

from fastapi import APIRouter, Depends, Form, status
from sqlalchemy.orm import Session

from ..auth import hash_password, mint_token, verify_password
from ..config import settings
from ..db import get_db
from ..errors import bad_request, unauthorized
from ..models import Customer
from ..schemas import Customer as CustomerSchema, ErrorResponse, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/auth/register", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> CustomerSchema:
    existing = db.query(Customer).filter(Customer.email == req.email).first()
    if existing:
        raise bad_request(f"Email {req.email} is already registered")

    customer = Customer(email=req.email, name=req.name, password_hash=hash_password(req.password))
    db.add(customer)
    db.flush()
    return CustomerSchema(id=customer.id, email=req.email, name=req.name)


@router.post("/oauth/token", response_model=TokenResponse, include_in_schema=False)
def token(
    grant_type: str = Form(...),
    username: str | None = Form(None),
    password: str | None = Form(None),
    client_id: str | None = Form(None),
    client_secret: str | None = Form(None),
    scope: str | None = Form(None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    if grant_type == "password":
        if not username or not password:
            raise bad_request("Missing username or password")
        customer = db.query(Customer).filter(Customer.email == username).first()
        if not customer or not verify_password(password, customer.password_hash):
            raise unauthorized("Invalid credentials")
        token = mint_token(customer.id, "customer")
        return TokenResponse(access_token=token, token_type="Bearer", expires_in=settings.token_expiry_seconds, scope="customer")
    elif grant_type == "client_credentials":
        if not client_id or not client_secret:
            raise bad_request("Missing client_id or client_secret")
        if client_id == settings.admin_client_id and client_secret == settings.admin_client_secret:
            token = mint_token(None, "admin")
            return TokenResponse(access_token=token, token_type="Bearer", expires_in=settings.token_expiry_seconds, scope="admin")
        else:
            raise unauthorized("Invalid client credentials")
    else:
        raise bad_request(f"Unsupported grant_type: {grant_type}")
