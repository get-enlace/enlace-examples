"""Cart resource endpoints.

- POST /carts (customer) — create an empty cart
- GET /carts/{cartId} (customer) — get cart and items
- POST /carts/{cartId}/items (customer) — add/update item in cart
- DELETE /carts/{cartId}/items/{productId} (customer) — remove item from cart
- POST /carts/{cartId}/checkout (customer) — create order + payment from cart
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_customer_id
from ..errors import bad_request, conflict, not_found
from ..models import Cart, CartItem, Order, OrderItem, Payment, Product
from ..schemas import (
    Cart as CartSchema,
    CartCheckoutResponse,
    CartItem as CartItemSchema,
    CartItemRequest,
    ErrorResponse,
    Order as OrderSchema,
    OrderItem as OrderItemSchema,
    Payment as PaymentSchema,
)

router = APIRouter(tags=["carts"])


@router.post(
    "/carts",
    response_model=CartSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def create_cart(
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    """Create an empty cart for the current customer."""
    cart = Cart(customer_id=customer_id, checked_out=False, created_at=datetime.utcnow())
    db.add(cart)
    await db.flush()  # Get the ID without committing
    cart_id = cart.id

    return CartSchema(
        id=cart_id,
        customerId=customer_id,
        items=[],
        createdAt=datetime.utcnow(),
    )


@router.get(
    "/carts/{cart_id}",
    response_model=CartSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_cart(
    cart_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    """Get a cart and its items (customer can only see their own)."""
    result = await db.execute(
        select(Cart).where(Cart.id == cart_id)
    )
    cart = result.scalars().first()

    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    # Get cart items
    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id)
    )
    items_rows = result.scalars().all()

    items = [
        CartItemSchema(productId=r.product_id, quantity=r.quantity)
        for r in items_rows
    ]

    return CartSchema(
        id=cart_id,
        customerId=cart.customer_id,
        items=items,
        createdAt=cart.created_at,
    )


@router.post(
    "/carts/{cart_id}/items",
    response_model=CartSchema,
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
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    """Add or update an item in the cart.

    If the product is already in the cart, increment its quantity.
    400 if the product doesn't exist.
    """
    # Verify cart belongs to customer
    result = await db.execute(
        select(Cart).where(Cart.id == cart_id)
    )
    cart = result.scalars().first()

    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    # Check product exists
    result = await db.execute(
        select(Product).where(Product.id == req.product_id)
    )
    product = result.scalars().first()

    if not product:
        raise bad_request(f"Product {req.product_id} not found")

    # Upsert cart item
    result = await db.execute(
        select(CartItem).where(
            (CartItem.cart_id == cart_id) & (CartItem.product_id == req.product_id)
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.quantity += req.quantity
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=req.product_id,
            quantity=req.quantity,
        )
        db.add(cart_item)

    await db.commit()

    # Return updated cart
    return await get_cart(cart_id, customer_id, db)


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
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove an item from the cart."""
    # Verify cart belongs to customer
    result = await db.execute(
        select(Cart).where(Cart.id == cart_id)
    )
    cart = result.scalars().first()

    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    # Delete the cart item
    result = await db.execute(
        select(CartItem).where(
            (CartItem.cart_id == cart_id) & (CartItem.product_id == product_id)
        )
    )
    cart_item = result.scalars().first()

    if cart_item:
        await db.delete(cart_item)
        await db.commit()


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
    db: AsyncSession = Depends(get_db),
) -> CartCheckoutResponse:
    """Checkout: create an Order and Payment from cart items.

    Creates the order with computed totals (unitPrice per item, total for order).
    400 if any product doesn't exist.
    409 if cart was already checked out.
    """
    # Verify cart belongs to customer
    result = await db.execute(
        select(Cart).where(Cart.id == cart_id)
    )
    cart = result.scalars().first()

    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    if cart.checked_out:
        raise conflict("Cart already checked out")

    # Get cart items
    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id)
    )
    items_rows = result.scalars().all()

    if not items_rows:
        raise bad_request("Cannot checkout an empty cart")

    # Compute totals (fetch current product prices)
    order_total = 0.0
    order_items_to_insert = []

    for item in items_rows:
        result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = result.scalars().first()

        if not product:
            raise bad_request(f"Product {item.product_id} not found")

        unit_price = product.price
        item_total = unit_price * item.quantity
        order_total += item_total

        order_items_to_insert.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": unit_price,
        })

    # Create order
    order = Order(
        customer_id=customer_id,
        cart_id=cart_id,
        status="pending_payment",
        total=order_total,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    await db.flush()  # Get the order ID
    order_id = order.id

    # Create order items
    for item in order_items_to_insert:
        order_item = OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
        )
        db.add(order_item)

    # Create payment
    payment = Payment(
        order_id=order_id,
        amount=order_total,
        status="pending",
    )
    db.add(payment)

    # Mark cart as checked out
    cart.checked_out = True

    await db.commit()

    # Build response
    order_obj = OrderSchema(
        id=order_id,
        customerId=customer_id,
        cartId=cart_id,
        status="pending_payment",
        items=[
            OrderItemSchema(
                productId=item["product_id"],
                quantity=item["quantity"],
                unitPrice=item["unit_price"],
            )
            for item in order_items_to_insert
        ],
        total=order_total,
        createdAt=datetime.utcnow(),
    )

    payment_obj = PaymentSchema(
        id=payment.id,
        orderId=order_id,
        amount=order_total,
        method=None,
        status="pending",
        confirmedAt=None,
    )

    return CartCheckoutResponse(order=order_obj, payment=payment_obj)
