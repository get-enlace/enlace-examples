"""Payment resource endpoints.

- GET /payments/{id} (customer) — get a payment
- POST /payments/{id}/confirm (customer) — confirm payment (cascades order to "paid")
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_customer_id
from ..errors import conflict, not_found
from ..schemas import ErrorResponse, Payment, PaymentConfirmRequest

router = APIRouter(tags=["payments"])


@router.get(
    "/payments/{id}",
    response_model=Payment,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_payment(
    id: int,
    customer_id: int = Depends(get_current_customer_id),
) -> Payment:
    """Get a payment (customer can only see payments for their own orders)."""
    payment = await database.fetch_one(
        """SELECT p.id, p.order_id, p.amount, p.method, p.status, p.confirmed_at
           FROM payments p
           JOIN orders o ON p.order_id = o.id
           WHERE p.id = :id AND o.customer_id = :customer_id""",
        values={"id": id, "customer_id": customer_id},
    )

    if not payment:
        raise not_found("Payment", id)

    return Payment(
        id=payment["id"],
        order_id=payment["order_id"],
        amount=payment["amount"],
        method=payment["method"],
        status=payment["status"],
        confirmed_at=payment["confirmed_at"],
    )


@router.post(
    "/payments/{id}/confirm",
    response_model=Payment,
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
) -> Payment:
    """Confirm a payment and cascade the order to 'paid'.

    400 if the payment is not in 'pending' status.
    """
    # Fetch payment (ensuring it belongs to this customer)
    payment = await database.fetch_one(
        """SELECT p.id, p.order_id, p.amount, p.method, p.status, p.confirmed_at
           FROM payments p
           JOIN orders o ON p.order_id = o.id
           WHERE p.id = :id AND o.customer_id = :customer_id""",
        values={"id": id, "customer_id": customer_id},
    )

    if not payment:
        raise not_found("Payment", id)

    if payment["status"] != "pending":
        raise conflict(f"Cannot confirm a payment in '{payment['status']}' status")

    # Update payment
    now = datetime.utcnow()
    await database.execute(
        """UPDATE payments
           SET status = 'succeeded', method = :method, confirmed_at = :confirmed_at
           WHERE id = :id""",
        values={
            "id": id,
            "method": req.method,
            "confirmed_at": now,
        },
    )

    # Cascade order to 'paid'
    await database.execute(
        """UPDATE orders SET status = 'paid'
           WHERE id = :order_id""",
        values={"order_id": payment["order_id"]},
    )

    return Payment(
        id=payment["id"],
        order_id=payment["order_id"],
        amount=payment["amount"],
        method=req.method,
        status="succeeded",
        confirmed_at=now,
    )
