"""Payment resource endpoints - using SQLAlchemy ORM."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_customer_id
from ..errors import conflict, not_found
from ..models import Order, Payment
from ..schemas import ErrorResponse, Payment as PaymentSchema
from ..schemas import PaymentConfirmRequest

router = APIRouter(tags=["payments"])


@router.get(
    "/payments/{id}",
    response_model=PaymentSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_payment(
    id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> PaymentSchema:
    """Get a payment (customer can only see payments for their own orders)."""
    result = await db.execute(
        select(Payment).where(Payment.id == id)
    )
    payment = result.scalars().first()

    if not payment:
        raise not_found("Payment", id)

    # Check authorization
    result = await db.execute(
        select(Order).where(Order.id == payment.order_id)
    )
    order = result.scalars().first()

    if not order or order.customer_id != customer_id:
        raise not_found("Payment", id)

    return PaymentSchema(
        id=payment.id,
        orderId=payment.order_id,
        amount=payment.amount,
        method=payment.method,
        status=payment.status,
        confirmedAt=payment.confirmed_at,
    )


@router.post(
    "/payments/{id}/confirm",
    response_model=PaymentSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def confirm_payment(
    id: int,
    req: PaymentConfirmRequest,
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> PaymentSchema:
    """Confirm a payment and cascade the order to 'paid'.

    400 if the payment is not in 'pending' status.
    """
    result = await db.execute(
        select(Payment).where(Payment.id == id)
    )
    payment = result.scalars().first()

    if not payment:
        raise not_found("Payment", id)

    # Check authorization
    result = await db.execute(
        select(Order).where(Order.id == payment.order_id)
    )
    order = result.scalars().first()

    if not order or order.customer_id != customer_id:
        raise not_found("Payment", id)

    if payment.status != "pending":
        raise conflict(f"Cannot confirm a payment in '{payment.status}' status")

    # Update payment
    now = datetime.utcnow()
    payment.status = "succeeded"
    payment.method = req.method
    payment.confirmed_at = now

    # Cascade order to 'paid'
    order.status = "paid"

    await db.commit()

    return PaymentSchema(
        id=payment.id,
        orderId=payment.order_id,
        amount=payment.amount,
        method=req.method,
        status="succeeded",
        confirmedAt=now,
    )
