"""Orders resource — see ../../../CONTRACT.md. References a Customer and one
or more Products; `unitPrice`/`total` are server-computed from each
product's *current* price at creation time — deliberately response-only
fields the client didn't send, to give the canvas something worth mapping
from a response into a later step.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from ..errors import not_found
from ..schemas import ErrorResponse, Order, OrderItem, OrderItemRequest, OrderRequest, OrderStatusRequest
from ..store import InMemoryStore, get_store

router = APIRouter(prefix="/orders", tags=["orders"])


def _resolve_items(items: list[OrderItemRequest], store: InMemoryStore) -> list[OrderItem]:
    """Looks up each requested product and freezes its *current* price onto
    the order line, so a later price change never retroactively changes
    what an existing order billed.
    """
    resolved: list[OrderItem] = []
    for item in items:
        product = store.products.get(item.product_id)
        if product is None:
            raise HTTPException(400, f"productId {item.product_id} does not exist.")
        resolved.append(
            OrderItem(product_id=item.product_id, quantity=item.quantity, unit_price=product.price)
        )
    return resolved


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@router.get("", operation_id="listOrders", summary="List orders")
def list_orders(store: InMemoryStore = Depends(get_store)) -> list[Order]:
    return list(store.orders.values())


@router.get(
    "/{id}",
    operation_id="getOrder",
    summary="Fetch an order by id",
    responses={404: {"model": ErrorResponse}},
)
def get_order(id: int, store: InMemoryStore = Depends(get_store)) -> Order:
    order = store.orders.get(id)
    if order is None:
        raise not_found("Order", id)
    return order


@router.post(
    "",
    operation_id="createOrder",
    summary="Create an order (references an existing customer + products)",
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
def create_order(body: OrderRequest, store: InMemoryStore = Depends(get_store)) -> Order:
    if body.customer_id not in store.customers:
        raise HTTPException(400, f"customerId {body.customer_id} does not exist.")

    items = _resolve_items(body.items, store)
    total = sum(item.unit_price * item.quantity for item in items)

    order = Order(
        id=store.next_id("order"),
        customer_id=body.customer_id,
        status="pending",
        items=items,
        total=total,
        created_at=_now_iso(),
    )
    store.orders[order.id] = order
    return order


@router.put(
    "/{id}/status",
    operation_id="updateOrderStatus",
    summary="Update an order's status",
    responses={404: {"model": ErrorResponse}},
)
def update_order_status(
    id: int, body: OrderStatusRequest, store: InMemoryStore = Depends(get_store)
) -> Order:
    order = store.orders.get(id)
    if order is None:
        raise not_found("Order", id)
    updated = order.model_copy(update={"status": body.status})
    store.orders[id] = updated
    return updated


@router.delete(
    "/{id}",
    operation_id="deleteOrder",
    summary="Delete an order",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
def delete_order(id: int, store: InMemoryStore = Depends(get_store)) -> None:
    if store.orders.pop(id, None) is None:
        raise not_found("Order", id)
