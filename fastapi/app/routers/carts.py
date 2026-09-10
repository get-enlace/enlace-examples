"""Cart resource endpoints.

- POST /carts (customer) — create an empty cart
- GET /carts/{cartId} (customer) — get cart and items
- POST /carts/{cartId}/items (customer) — add/update item in cart
- DELETE /carts/{cartId}/items/{productId} (customer) — remove item from cart
- POST /carts/{cartId}/checkout (customer) — create order + payment from cart
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_customer_id
from ..errors import bad_request, conflict, not_found
from ..schemas import Cart, CartCheckoutResponse, CartItem, CartItemRequest, ErrorResponse, Order, OrderItem, Payment

router = APIRouter(tags=["carts"])


@router.post(
    "/carts",
    response_model=Cart,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def create_cart(customer_id: int = Depends(get_current_customer_id)) -> Cart:
    """Create an empty cart for the current customer."""
    cart_id = await database.execute(
        "INSERT INTO carts (customer_id, checked_out) VALUES (:customer_id, 0)",
        values={"customer_id": customer_id},
    )

    return Cart(
        id=cart_id,
        customer_id=customer_id,
        items=[],
        created_at=datetime.utcnow(),
    )


@router.get(
    "/carts/{cart_id}",
    response_model=Cart,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_cart(
    cart_id: int,
    customer_id: int = Depends(get_current_customer_id),
) -> Cart:
    """Get a cart and its items (customer can only see their own)."""
    cart = await database.fetch_one(
        "SELECT id, customer_id, created_at FROM carts WHERE id = :id",
        values={"id": cart_id},
    )
    if not cart or cart["customer_id"] != customer_id:
        raise not_found("Cart", cart_id)

    items_rows = await database.fetch_all(
        """SELECT product_id, quantity FROM cart_items
           WHERE cart_id = :cart_id
           ORDER BY product_id""",
        values={"cart_id": cart_id},
    )

    items = [CartItem(product_id=r["product_id"], quantity=r["quantity"]) for r in items_rows]

    return Cart(
        id=cart_id,
        customer_id=cart["customer_id"],
        items=items,
        created_at=cart["created_at"],
    )


@router.post(
    "/carts/{cart_id}/items",
    response_model=Cart,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def add_cart_item(
    cart_id: int,
    req: CartItemRequest,
    customer_id: int = Depends(get_current_customer_id),
) -> Cart:
    """Add or update an item in the cart.

    If the product is already in the cart, increment its quantity.
    400 if the product doesn't exist.
    """
    # Verify cart belongs to customer
    cart = await database.fetch_one(
        "SELECT id, customer_id FROM carts WHERE id = :id",
        values={"id": cart_id},
    )
    if not cart or cart["customer_id"] != customer_id:
        raise not_found("Cart", cart_id)

    # Check product exists
    product = await database.fetch_one(
        "SELECT id FROM products WHERE id = :id",
        values={"id": req.product_id},
    )
    if not product:
        raise bad_request(f"Product {req.product_id} not found")

    # Upsert cart item
    existing = await database.fetch_one(
        "SELECT quantity FROM cart_items WHERE cart_id = :cart_id AND product_id = :product_id",
        values={"cart_id": cart_id, "product_id": req.product_id},
    )

    if existing:
        await database.execute(
            """UPDATE cart_items SET quantity = quantity + :qty
               WHERE cart_id = :cart_id AND product_id = :product_id""",
            values={"qty": req.quantity, "cart_id": cart_id, "product_id": req.product_id},
        )
    else:
        await database.execute(
            """INSERT INTO cart_items (cart_id, product_id, quantity)
               VALUES (:cart_id, :product_id, :quantity)""",
            values={
                "cart_id": cart_id,
                "product_id": req.product_id,
                "quantity": req.quantity,
            },
        )

    # Return updated cart
    return await get_cart(cart_id, customer_id)


@router.delete(
    "/carts/{cart_id}/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def remove_cart_item(
    cart_id: int,
    product_id: int,
    customer_id: int = Depends(get_current_customer_id),
) -> None:
    """Remove an item from the cart."""
    # Verify cart belongs to customer
    cart = await database.fetch_one(
        "SELECT id, customer_id FROM carts WHERE id = :id",
        values={"id": cart_id},
    )
    if not cart or cart["customer_id"] != customer_id:
        raise not_found("Cart", cart_id)

    await database.execute(
        """DELETE FROM cart_items
           WHERE cart_id = :cart_id AND product_id = :product_id""",
        values={"cart_id": cart_id, "product_id": product_id},
    )


@router.post(
    "/carts/{cart_id}/checkout",
    response_model=CartCheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def checkout_cart(
    cart_id: int,
    customer_id: int = Depends(get_current_customer_id),
) -> CartCheckoutResponse:
    """Checkout: create an Order and Payment from cart items.

    Creates the order with computed totals (unitPrice per item, total for order).
    400 if any product doesn't exist.
    409 if cart was already checked out.
    """
    # Verify cart belongs to customer
    cart = await database.fetch_one(
        "SELECT id, customer_id, checked_out FROM carts WHERE id = :id",
        values={"id": cart_id},
    )
    if not cart or cart["customer_id"] != customer_id:
        raise not_found("Cart", cart_id)

    if cart["checked_out"]:
        raise conflict("Cart already checked out")

    # Get cart items
    items_rows = await database.fetch_all(
        "SELECT product_id, quantity FROM cart_items WHERE cart_id = :cart_id",
        values={"cart_id": cart_id},
    )

    if not items_rows:
        raise bad_request("Cannot checkout an empty cart")

    # Compute totals (fetch current product prices)
    order_total = 0.0
    order_items_to_insert = []

    for item in items_rows:
        product = await database.fetch_one(
            "SELECT price FROM products WHERE id = :id",
            values={"id": item["product_id"]},
        )
        if not product:
            raise bad_request(f"Product {item['product_id']} not found")

        unit_price = product["price"]
        item_total = unit_price * item["quantity"]
        order_total += item_total

        order_items_to_insert.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": unit_price,
        })

    # Create order
    order_id = await database.execute(
        """INSERT INTO orders (customer_id, cart_id, status, total)
           VALUES (:customer_id, :cart_id, 'pending_payment', :total)""",
        values={
            "customer_id": customer_id,
            "cart_id": cart_id,
            "total": order_total,
        },
    )

    # Create order items
    for item in order_items_to_insert:
        await database.execute(
            """INSERT INTO order_items (order_id, product_id, quantity, unit_price)
               VALUES (:order_id, :product_id, :quantity, :unit_price)""",
            values={
                "order_id": order_id,
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            },
        )

    # Create payment
    payment_id = await database.execute(
        """INSERT INTO payments (order_id, amount, status)
           VALUES (:order_id, :amount, 'pending')""",
        values={
            "order_id": order_id,
            "amount": order_total,
        },
    )

    # Mark cart as checked out
    await database.execute(
        "UPDATE carts SET checked_out = 1 WHERE id = :id",
        values={"id": cart_id},
    )

    # Build response
    order_obj = Order(
        id=order_id,
        customer_id=customer_id,
        cart_id=cart_id,
        status="pending_payment",
        items=[
            OrderItem(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            for item in order_items_to_insert
        ],
        total=order_total,
        created_at=datetime.utcnow(),
    )

    payment_obj = Payment(
        id=payment_id,
        order_id=order_id,
        amount=order_total,
        method=None,
        status="pending",
        confirmed_at=None,
    )

    return CartCheckoutResponse(order=order_obj, payment=payment_obj)
