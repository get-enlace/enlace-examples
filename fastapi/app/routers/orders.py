"""Order resource endpoints - using SQLAlchemy ORM."""

import hashlib
import time
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_admin_id, get_current_customer_id, get_customer_or_admin
from ..errors import conflict, not_found
from ..models import Order, OrderItem as OrderItemModel, Shipment
from ..schemas import ErrorResponse, Order as OrderSchema
from ..schemas import OrderItem, Shipment as ShipmentSchema

router = APIRouter(tags=["orders"])


def _fetch_order_with_items(
    order: Order, db: Session
) -> OrderSchema:
    """Helper to fetch an order with its items."""
    result = db.execute(
        select(OrderItemModel).where(OrderItemModel.order_id == order.id)
    )
    items_rows = result.scalars().all()

    items = [
        OrderItem(
            productId=r.product_id,
            quantity=r.quantity,
            unitPrice=r.unit_price,
        )
        for r in items_rows
    ]

    return OrderSchema(
        id=order.id,
        customerId=order.customer_id,
        cartId=order.cart_id,
        status=order.status,
        items=items,
        total=order.total,
        createdAt=order.created_at,
    )


@router.get(
    "/orders",
    response_model=list[OrderSchema],
    responses={
        401: {"model": ErrorResponse},
    },
)
def list_orders(
    actor: dict = Depends(get_customer_or_admin),
    db: Session = Depends(get_db),
) -> list[OrderSchema]:
    """List orders.

    Customer credential: sees only their own orders.
    Admin credential: sees all orders.
    """
    if actor["type"] == "customer":
        result = db.execute(
            select(Order).where(Order.customer_id == actor["id"]).order_by(Order.id)
        )
    else:
        result = db.execute(select(Order).order_by(Order.id))

    orders_rows = result.scalars().all()

    orders = []
    for order in orders_rows:
        order_schema = _fetch_order_with_items(order, db)
        orders.append(order_schema)

    return orders


@router.get(
    "/orders/{id}",
    response_model=OrderSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def get_order(
    id: int,
    actor: dict = Depends(get_customer_or_admin),
    db: Session = Depends(get_db),
) -> OrderSchema:
    """Get an order.

    Customer credential: can only see their own (404 if not theirs).
    Admin credential: can see any.
    """
    result = db.execute(select(Order).where(Order.id == id))
    order = result.scalars().first()

    if not order:
        raise not_found("Order", id)

    # Authorization check
    if actor["type"] == "customer" and order.customer_id != actor["id"]:
        raise not_found("Order", id)

    return _fetch_order_with_items(order, db)


@router.post(
    "/orders/{id}/cancel",
    response_model=OrderSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def cancel_order(
    id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> OrderSchema:
    """Cancel an order (customer only).

    Only works if order status is 'pending_payment'. Cascades order to 'cancelled'.
    """
    result = db.execute(select(Order).where(Order.id == id))
    order = result.scalars().first()

    if not order or order.customer_id != customer_id:
        raise not_found("Order", id)

    if order.status != "pending_payment":
        raise conflict(f"Cannot cancel an order in '{order.status}' status (must be 'pending_payment')")

    # Cascade order to 'cancelled'
    order.status = "cancelled"
    db.commit()

    # Return updated order
    return get_order(id, {"type": "customer", "id": customer_id}, db)


@router.post(
    "/orders/{id}/fulfill",
    response_model=ShipmentSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def fulfill_order(
    id: int,
    _admin: bool = Depends(get_current_admin_id),
    db: Session = Depends(get_db),
) -> ShipmentSchema:
    """Fulfill an order and create a shipment (admin only).

    Only works if order status is 'paid'.
    Creates a shipment with a generated tracking number and cascades order to 'shipped'.
    """
    result = db.execute(select(Order).where(Order.id == id))
    order = result.scalars().first()

    if not order:
        raise not_found("Order", id)

    if order.status != "paid":
        raise conflict(f"Cannot fulfill an order in '{order.status}' status (must be 'paid')")

    # Generate tracking number (simple format: TRK-<timestamp-based>)
    tracking = f"TRK-{hashlib.md5(f'{id}-{int(time.time())}'.encode()).hexdigest()[:8].upper()}"

    # Create shipment
    shipment = Shipment(
        order_id=id,
        tracking_number=tracking,
        carrier="DemoShip Express",
        status="in_transit",
        created_at=datetime.utcnow(),
    )
    db.add(shipment)

    # Cascade order to 'shipped'
    order.status = "shipped"

    db.commit()
    db.refresh(shipment)

    return ShipmentSchema(
        id=shipment.id,
        orderId=id,
        trackingNumber=tracking,
        carrier="DemoShip Express",
        status="in_transit",
        createdAt=datetime.utcnow(),
    )
