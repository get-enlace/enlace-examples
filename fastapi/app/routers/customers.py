"""Customer resource endpoints.

- GET /customers (admin only) — all customers
- GET /customers/{id} (admin only) — one customer
- GET /customers/me (customer) — current customer's own profile
- PUT /customers/me (customer) — update current customer's name/email
"""

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_admin_id, get_current_customer_id
from ..errors import not_found
from ..schemas import Customer, CustomerMeUpdate, ErrorResponse

router = APIRouter(tags=["customers"])


@router.get(
    "/customers",
    response_model=list[Customer],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def list_customers(_admin: bool = Depends(get_current_admin_id)) -> list[Customer]:
    """List all customers (admin only)."""
    rows = await database.fetch_all("SELECT id, email, name FROM customers ORDER BY id")
    return [Customer(id=r["id"], email=r["email"], name=r["name"]) for r in rows]


@router.get(
    "/customers/{id}",
    response_model=Customer,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_customer(id: int, _admin: bool = Depends(get_current_admin_id)) -> Customer:
    """Get a specific customer (admin only)."""
    row = await database.fetch_one(
        "SELECT id, email, name FROM customers WHERE id = :id",
        values={"id": id},
    )
    if not row:
        raise not_found("Customer", id)
    return Customer(id=row["id"], email=row["email"], name=row["name"])


@router.get(
    "/customers/me",
    response_model=Customer,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def get_current_customer(customer_id: int = Depends(get_current_customer_id)) -> Customer:
    """Get current customer's own profile."""
    row = await database.fetch_one(
        "SELECT id, email, name FROM customers WHERE id = :id",
        values={"id": customer_id},
    )
    if not row:
        raise not_found("Customer", customer_id)
    return Customer(id=row["id"], email=row["email"], name=row["name"])


@router.put(
    "/customers/me",
    response_model=Customer,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def update_current_customer(
    req: CustomerMeUpdate,
    customer_id: int = Depends(get_current_customer_id),
) -> Customer:
    """Update current customer's profile (name/email only)."""
    # Fetch current customer
    current = await database.fetch_one(
        "SELECT id, email, name FROM customers WHERE id = :id",
        values={"id": customer_id},
    )
    if not current:
        raise not_found("Customer", customer_id)

    # Update fields (null means don't change)
    email = req.email if req.email is not None else current["email"]
    name = req.name if req.name is not None else current["name"]

    await database.execute(
        "UPDATE customers SET email = :email, name = :name WHERE id = :id",
        values={"email": email, "name": name, "id": customer_id},
    )

    return Customer(id=customer_id, email=email, name=name)
