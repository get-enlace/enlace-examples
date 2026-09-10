"""Pydantic request/response models for every resource — see ../../CONTRACT.md.

Python attributes use snake_case; JSON in/out is camelCase via
CamelModel's alias generator (mirroring how aspnetcore/nest translate
their own idioms to the shared wire format).

These are the source of truth for OpenAPI auto-generation — FastAPI
extracts schema from the models you use in @app.post/@app.get/etc.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Status enumerations (per CONTRACT.md)
OrderStatus = Literal["pending_payment", "paid", "shipped", "delivered", "cancelled"]
PaymentStatus = Literal["pending", "succeeded"]
ShipmentStatus = Literal["in_transit", "delivered"]
PaymentMethod = Literal["card", "paypal"]


class CamelModel(BaseModel):
    """Base Pydantic model with snake_case -> camelCase alias generator."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ErrorResponse(CamelModel):
    error: str


# --- Auth ----------------------------------------------------------------


class RegisterRequest(CamelModel):
    name: str
    email: str
    password: str


class LoginRequest(CamelModel):
    email: str
    password: str


class TokenResponse(CamelModel):
    """OAuth2 RFC 6749 compliant token response."""
    access_token: str
    token_type: str  # always "Bearer"
    expires_in: int  # in seconds
    scope: str  # "customer" or "admin"


# --- Customers -----------------------------------------------------------


class CustomerRequest(CamelModel):
    name: str
    email: str


class Customer(CustomerRequest):
    id: int


class CustomerMeUpdate(CamelModel):
    name: str | None = None
    email: str | None = None


# --- Products ------------------------------------------------------------


class ProductRequest(CamelModel):
    name: str
    price: float
    stock: int


class Product(ProductRequest):
    id: int


# --- Carts ---------------------------------------------------------------


class CartItemRequest(CamelModel):
    product_id: int
    quantity: int


class CartItem(CartItemRequest):
    pass


class CartRequest(CamelModel):
    pass  # POST /carts takes no body


class Cart(CamelModel):
    id: int
    customer_id: int
    items: list[CartItem]
    created_at: datetime


class CartCheckoutResponse(CamelModel):
    """Response from POST /carts/{cartId}/checkout — creates order + payment."""
    order: Order
    payment: Payment


# --- Orders --------------------------------------------------------------


class OrderItemRequest(CamelModel):
    product_id: int
    quantity: int


class OrderItem(OrderItemRequest):
    unit_price: float


class OrderRequest(CamelModel):
    customer_id: int
    items: list[OrderItemRequest]


class OrderStatusRequest(CamelModel):
    status: OrderStatus


class Order(CamelModel):
    id: int
    customer_id: int
    cart_id: int
    status: OrderStatus
    items: list[OrderItem]
    total: float
    created_at: datetime


class OrderCancelRequest(CamelModel):
    pass  # POST /orders/{id}/cancel takes no body


class OrderFulfillRequest(CamelModel):
    pass  # POST /orders/{id}/fulfill takes no body


# --- Payments ------------------------------------------------------------


class PaymentConfirmRequest(CamelModel):
    method: PaymentMethod


class Payment(CamelModel):
    id: int
    order_id: int
    amount: float
    method: PaymentMethod | None = None
    status: PaymentStatus
    confirmed_at: datetime | None = None


# --- Shipments -----------------------------------------------------------


class ShipmentStatusRequest(CamelModel):
    status: ShipmentStatus


class Shipment(CamelModel):
    id: int
    order_id: int
    tracking_number: str
    carrier: str
    status: ShipmentStatus
    created_at: datetime
