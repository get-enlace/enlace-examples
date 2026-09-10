"""Contract schemas — see ../../CONTRACT.md. One module for every resource's
request/response shape, mirroring how `nest`'s `dto.ts` keeps its DTOs
together rather than splitting them per-resource.

Python attributes stay idiomatic snake_case; JSON in/out is camelCase, via
`CamelModel`'s alias generator. Mirrors what `aspnetcore` (PascalCase C#
records, camelCase on the wire via ASP.NET Core's default JSON policy) and
`nest` (`@ApiProperty`-annotated DTO classes) do for this same contract,
each via their own framework/language's own naming convention translated
to the one wire shape every example must produce.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

OrderStatus = Literal["pending", "paid", "shipped", "cancelled"]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ErrorResponse(CamelModel):
    error: str


# --- Customers ---------------------------------------------------------


class CustomerRequest(CamelModel):
    name: str
    email: str


class Customer(CustomerRequest):
    id: int


# --- Products ------------------------------------------------------------


class ProductRequest(CamelModel):
    name: str
    price: float
    stock: int


class Product(ProductRequest):
    id: int


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
    status: OrderStatus
    items: list[OrderItem]
    total: float
    created_at: str
