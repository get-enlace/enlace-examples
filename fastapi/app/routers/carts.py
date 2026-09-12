"""Cart resource endpoints - synchronous SQLAlchemy ORM."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
    responses={401: {"model": ErrorResponse}},
)
def create_cart(
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> CartSchema:
    """Create an empty cart for the current customer."""
    cart = Cart(customer_id=customer_id, checked_out=False, created_at=datetime.utcnow())
    db.add(cart)
    db.flush()
    cart_id = cart.id
    db.commit()

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
def get_cart(
    cart_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> CartSchema:
    """Get a cart and its items (customer can only see their own)."""
    cart = db.query(Cart).filter(Cart.id == cart_id).first()

    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    items_rows = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
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
def add_cart_item(
    cart_id: int,
    req: CartItemRequest,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> CartSchema:
    """Add or update an item in the cart."""
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise bad_request(f"Product {req.product_id} not found")

    existing = db.query(CartItem).filter(
        (CartItem.cart_id == cart_id) & (CartItem.product_id == req.product_id)
    ).first()

    if existing:
        existing.quantity += req.quantity
    else:
        db.add(CartItem(cart_id=cart_id, product_id=req.product_id, quantity=req.quantity))

    db.commit()
    return get_cart(cart_id, customer_id, db)


@router.delete(
    "/carts/{cart_id}/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def remove_cart_item(
    cart_id: int,
    product_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> None:
    """Remove an item from the cart."""
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    cart_item = db.query(CartItem).filter(
        (CartItem.cart_id == cart_id) & (CartItem.product_id == product_id)
    ).first()

    if cart_item:
        db.delete(cart_item)
        db.commit()


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
def checkout_cart(
    cart_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> CartCheckoutResponse:
    """Checkout: create an Order and Payment from cart items."""
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart or cart.customer_id != customer_id:
        raise not_found("Cart", cart_id)

    if cart.checked_out:
        raise conflict("Cart already checked out")

    items_rows = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items_rows:
        raise bad_request("Cannot checkout an empty cart")

    order_total = 0.0
    order_items_to_insert = []

    for item in items_rows:
        product = db.query(Product).filter(Product.id == item.product_id).first()
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

    order = Order(
        customer_id=customer_id,
        cart_id=cart_id,
        status="pending_payment",
        total=order_total,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()
    order_id = order.id

    for item in order_items_to_insert:
        db.add(OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
        ))

    payment = Payment(
        order_id=order_id,
        amount=order_total,
        status="pending",
    )
    db.add(payment)

    cart.checked_out = True
    db.commit()

    return CartCheckoutResponse(
        order=OrderSchema(
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
        ),
        payment=PaymentSchema(
            id=payment.id,
            orderId=order_id,
            amount=order_total,
            method=None,
            status="pending",
            confirmedAt=None,
        ),
    )
