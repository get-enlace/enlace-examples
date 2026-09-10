"""Import and expose all routers for registration in main.py."""

from . import auth, carts, customers, orders, payments, products, shipments

__all__ = [
    "auth",
    "customers",
    "products",
    "carts",
    "orders",
    "payments",
    "shipments",
]
