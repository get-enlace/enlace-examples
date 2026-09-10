"""Order resource endpoints.

- GET /orders (customer or admin) — customer sees own only, admin sees all
- GET /orders/{id} (customer or admin) — customer can only see own, admin sees any
- POST /orders/{id}/cancel (customer) — cancel an order (only from pending_payment)
- POST /orders/{id}/fulfill (admin) — fulfill order, create shipment (only from paid)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_admin_id, get_current_customer_id, get_customer_or_admin
from ..errors import conflict, not_found
from ..schemas import ErrorResponse, Order, OrderItem, Shipment

router = APIRouter(tags=["orders"])


@router.get(
    "/orders",
    response_model=list[Order],
    responses={
        401: {"model": ErrorResponse},
    },
)
async def list_orders(actor: dict = Depends(get_customer_or_admin)) -> list[Order]:
    """List orders.

    Customer credential: sees only their own orders.
    Admin credential: sees all orders.
    """
    if actor["type"] == "customer":
        query = """SELECT id, customer_id, cart_id, status, total, created_at
                   FROM orders
                   WHERE customer_id = :customer_id
                   ORDER BY id"""
        orders_rows = await database.fetch_all(query, values={"customer_id": actor["id"]})
    else:
        query = """SELECT id, customer_id, cart_id, status, total, created_at
                   FROM orders
                   ORDER BY id"""
        orders_rows = await database.fetch_all(query)

    orders = []
    for order_row in orders_rows:
        items_rows = await database.fetch_all(
            """SELECT product_id, quantity, unit_price FROM order_items
               WHERE order_id = :order_id
               ORDER BY product_id""",
            values={"order_id": order_row["id"]},
        )
        items = [
            OrderItem(
                product_id=r["product_id"],
                quantity=r["quantity"],
                unit_price=r["unit_price"],
            )
            for r in items_rows
        ]
        orders.append(
            Order(
                id=order_row["id"],
                customer_id=order_row["customer_id"],
                cart_id=order_row["cart_id"],
                status=order_row["status"],
                items=items,
                total=order_row["total"],
                created_at=order_row["created_at"],
            )
        )

    return orders


@router.get(
    "/orders/{id}",
    response_model=Order,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_order(id: int, actor: dict = Depends(get_customer_or_admin)) -> Order:
    """Get an order.

    Customer credential: can only see their own (404 if not theirs).
    Admin credential: can see any.
    """
    order_row = await database.fetch_one(
        """SELECT id, customer_id, cart_id, status, total, created_at
           FROM orders
           WHERE id = :id""",
        values={"id": id},
    )

    if not order_row:
        raise not_found("Order", id)

    # Authorization check
    if actor["type"] == "customer" and order_row["customer_id"] != actor["id"]:
        raise not_found("Order", id)

    items_rows = await database.fetch_all(
        """SELECT product_id, quantity, unit_price FROM order_items
           WHERE order_id = :order_id
           ORDER BY product_id""",
        values={"order_id": id},
    )

    items = [
        OrderItem(
            product_id=r["product_id"],
            quantity=r["quantity"],
            unit_price=r["unit_price"],
        )
        for r in items_rows
    ]

    return Order(
        id=order_row["id"],
        customer_id=order_row["customer_id"],
        cart_id=order_row["cart_id"],
        status=order_row["status"],
        items=items,
        total=order_row["total"],
        created_at=order_row["created_at"],
    )


@router.post(
    "/orders/{id}/cancel",
    response_model=Order,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def cancel_order(
    id: int,
    customer_id: int = Depends(get_current_customer_id),
) -> Order:
    """Cancel an order (customer only).

    Only works if order status is 'pending_payment'. Cascades order to 'cancelled'.
    """
    order_row = await database.fetch_one(
        "SELECT id, status, customer_id FROM orders WHERE id = :id",
        values={"id": id},
    )

    if not order_row or order_row["customer_id"] != customer_id:
        raise not_found("Order", id)

    if order_row["status"] != "pending_payment":
        raise conflict(f"Cannot cancel an order in '{order_row['status']}' status (must be 'pending_payment')")

    # Cascade order to 'cancelled'
    await database.execute(
        "UPDATE orders SET status = 'cancelled' WHERE id = :id",
        values={"id": id},
    )

    # Return updated order
    return await get_order(id, {"type": "customer", "id": customer_id})


@router.post(
    "/orders/{id}/fulfill",
    response_model=Shipment,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def fulfill_order(
    id: int,
    _admin: bool = Depends(get_current_admin_id),
) -> Shipment:
    """Fulfill an order and create a shipment (admin only).

    Only works if order status is 'paid'.
    Creates a shipment with a generated tracking number and cascades order to 'shipped'.
    """
    order = await database.fetch_one(
        "SELECT id, status FROM orders WHERE id = :id",
        values={"id": id},
    )

    if not order:
        raise not_found("Order", id)

    if order["status"] != "paid":
        raise conflict(f"Cannot fulfill an order in '{order['status']}' status (must be 'paid')")

    # Generate tracking number (simple format: TRK-<timestamp-based>)
    import hashlib
    import time

    tracking = f"TRK-{hashlib.md5(f'{id}-{int(time.time())}'.encode()).hexdigest()[:8].upper()}"

    # Create shipment
    shipment_id = await database.execute(
        """INSERT INTO shipments (order_id, tracking_number, carrier, status)
           VALUES (:order_id, :tracking_number, 'DemoShip Express', 'in_transit')""",
        values={
            "order_id": id,
            "tracking_number": tracking,
        },
    )

    # Cascade order to 'shipped'
    await database.execute(
        "UPDATE orders SET status = 'shipped' WHERE id = :id",
        values={"id": id},
    )

    return Shipment(
        id=shipment_id,
        order_id=id,
        tracking_number=tracking,
        carrier="DemoShip Express",
        status="in_transit",
        created_at=datetime.utcnow(),
    )
