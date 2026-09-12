"""Customer resource endpoints - using SQLAlchemy ORM."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_admin_id, get_current_customer_id
from ..errors import not_found
from ..models import Customer
from ..schemas import Customer as CustomerSchema
from ..schemas import CustomerMeUpdate, ErrorResponse

router = APIRouter(tags=["customers"])


@router.get(
    "/customers",
    response_model=list[CustomerSchema],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def list_customers(
    _admin: bool = Depends(get_current_admin_id),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerSchema]:
    """List all customers (admin only)."""
    result = await db.execute(select(Customer).order_by(Customer.id))
    customers = result.scalars().all()
    return [CustomerSchema(id=c.id, email=c.email, name=c.name) for c in customers]


@router.get(
    "/customers/{id}",
    response_model=CustomerSchema,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_customer(
    id: int,
    _admin: bool = Depends(get_current_admin_id),
    db: AsyncSession = Depends(get_db),
) -> CustomerSchema:
    """Get a specific customer (admin only)."""
    result = await db.execute(select(Customer).where(Customer.id == id))
    customer = result.scalars().first()
    if not customer:
        raise not_found("Customer", id)
    return CustomerSchema(id=customer.id, email=customer.email, name=customer.name)


@router.get(
    "/customers/me",
    response_model=CustomerSchema,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def get_current_customer(
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> CustomerSchema:
    """Get current customer's own profile."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise not_found("Customer", customer_id)
    return CustomerSchema(id=customer.id, email=customer.email, name=customer.name)


@router.put(
    "/customers/me",
    response_model=CustomerSchema,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def update_current_customer(
    req: CustomerMeUpdate,
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> CustomerSchema:
    """Update current customer's profile (name/email only)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise not_found("Customer", customer_id)

    # Update fields (null means don't change)
    if req.email is not None:
        customer.email = req.email
    if req.name is not None:
        customer.name = req.name

    await db.commit()

    return CustomerSchema(id=customer.id, email=customer.email, name=customer.name)
