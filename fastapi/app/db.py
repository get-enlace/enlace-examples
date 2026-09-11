"""Database setup — SQLAlchemy ORM + async databases for query execution.

Schema is defined as DDL strings here (no migrations), seeded with fixtures
on app startup. Async-only: SQLAlchemy's new async API (sessionmaker +
AsyncSession) + databases for lower-level async execute().
"""

from datetime import datetime
from typing import AsyncGenerator

from databases import Database
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# ORM base — all models inherit from this
Base = declarative_base()

# Async database connection (used for migrations, seeding, and in routes via dependency)
database = Database(settings.database_url)


async def init_db() -> None:
    """Initialize database: create tables, seed fixtures (upsert-if-missing)."""
    await database.connect()

    # Create tables from raw SQL schema
    for statement in SCHEMA_DDL.split(';'):
        statement = statement.strip()
        if statement:
            await database.execute(statement)

    # Seed fixtures (upsert-if-missing)
    await seed_fixtures()


async def close_db() -> None:
    """Close the database connection."""
    await database.disconnect()


def get_session_factory() -> sessionmaker:
    """Return a sessionmaker bound to the async engine."""
    engine = create_async_engine(settings.database_url, echo=False)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield a database session for each request."""
    async_session = get_session_factory()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# Schema DDL (no migrations, just raw SQL executed on startup)
# =============================================================================

SCHEMA_DDL = """
-- Customers (register or seeded demo customer)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Products (admin-managed catalog)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Carts (per customer, transient until checkout)
CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    checked_out BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Cart items (many-to-many: cart -> product)
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(cart_id, product_id)
);

-- Orders (created from a cart at checkout)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    cart_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_payment',  -- pending_payment | paid | shipped | delivered | cancelled
    total REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (cart_id) REFERENCES carts(id)
);

-- Order items (many-to-many: order -> product, with captured unit price)
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Payments (created alongside order at checkout)
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL,
    method TEXT,  -- 'card' | 'paypal' | null
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | succeeded
    confirmed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Shipments (created when order is fulfilled)
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE,
    tracking_number TEXT NOT NULL UNIQUE,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_transit',  -- in_transit | delivered
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- OAuth2 tokens (server-side cache for opaque tokens)
CREATE TABLE IF NOT EXISTS oauth_tokens (
    token TEXT PRIMARY KEY,
    customer_id INTEGER,  -- null if this is an admin token (no associated customer)
    token_type TEXT NOT NULL,  -- 'customer' | 'admin'
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""


async def seed_fixtures() -> None:
    """Seed demo fixtures (upsert-if-missing) on startup.

    Import here to avoid circular imports (models need settings, auth needs models).
    """
    from .auth import hash_password
    from .models import Customer

    # Demo customer (if not already present)
    existing_customer = await database.fetch_one(
        "SELECT id FROM customers WHERE email = :email",
        values={"email": settings.demo_customer_email},
    )
    if not existing_customer:
        await database.execute(
            """INSERT INTO customers (email, name, password_hash, created_at)
               VALUES (:email, :name, :password_hash, :created_at)""",
            values={
                "email": settings.demo_customer_email,
                "name": "Demo Customer",
                "password_hash": hash_password(settings.demo_customer_password),
                "created_at": datetime.utcnow(),
            },
        )

    # Demo products (if not already present)
    existing_products = await database.fetch_all("SELECT id FROM products")
    if not existing_products:
        await database.execute_many(
            """INSERT INTO products (name, price, stock, created_at)
               VALUES (:name, :price, :stock, :created_at)""",
            [
                {
                    "name": "Mechanical Keyboard",
                    "price": 129.99,
                    "stock": 42,
                    "created_at": datetime.utcnow(),
                },
                {
                    "name": "Wireless Mouse",
                    "price": 59.99,
                    "stock": 100,
                    "created_at": datetime.utcnow(),
                },
                {
                    "name": "USB-C Hub",
                    "price": 49.99,
                    "stock": 75,
                    "created_at": datetime.utcnow(),
                },
            ],
        )
