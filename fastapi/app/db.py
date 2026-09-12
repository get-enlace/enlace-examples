"""Database setup — SQLAlchemy ORM with async support.

Uses SQLAlchemy 2.0+ async engine and sessions. Schema is defined as DDL
strings (no migrations), seeded with fixtures on app startup.
"""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# ORM base — all models inherit from this
Base = declarative_base()

# Global async engine (created once, shared across app)
_engine = None


def get_engine():
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,  # Set to True to see SQL queries
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    """Return a sessionmaker for async sessions."""
    return sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield a database session for each request."""
    async_session = get_session_factory()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database: create tables, seed fixtures (upsert-if-missing)."""
    async with get_engine().begin() as conn:
        # Create tables from PostgreSQL schema DDL
        for statement in SCHEMA_DDL.split(';'):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
        await conn.commit()

    # Seed fixtures (upsert-if-missing)
    await seed_fixtures()


async def close_db() -> None:
    """Close the database connection."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


# =============================================================================
# PostgreSQL Schema DDL (no migrations, just raw SQL executed on startup)
# =============================================================================

SCHEMA_DDL = """
-- Customers (register or seeded demo customer)
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Products (admin-managed catalog)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Carts (per customer, transient until checkout)
CREATE TABLE IF NOT EXISTS carts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    checked_out BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Cart items (many-to-many: cart -> product)
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(cart_id, product_id)
);

-- Orders (created from a cart at checkout)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    cart_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_payment',
    total REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (cart_id) REFERENCES carts(id)
);

-- Order items (many-to-many: order -> product, with captured unit price)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Payments (created alongside order at checkout)
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL,
    method TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    confirmed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Shipments (created when order is fulfilled)
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE,
    tracking_number TEXT NOT NULL UNIQUE,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_transit',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- OAuth2 tokens (server-side cache for opaque tokens)
CREATE TABLE IF NOT EXISTS oauth_tokens (
    token TEXT PRIMARY KEY,
    customer_id INTEGER,
    token_type TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""


async def seed_fixtures() -> None:
    """Seed demo fixtures (upsert-if-missing) on startup.

    Uses SQLAlchemy ORM to insert data safely and type-checked.
    """
    from .auth import hash_password
    from .models import Customer, Product

    async_session = get_session_factory()

    async with async_session() as session:
        from sqlalchemy import select

        # Demo customer (if not already present)
        result = await session.execute(
            select(Customer).where(Customer.email == settings.demo_customer_email)
        )
        existing_customer = result.scalars().first()

        if not existing_customer:
            demo_customer = Customer(
                email=settings.demo_customer_email,
                name="Demo Customer",
                password_hash=hash_password(settings.demo_customer_password),
                created_at=datetime.utcnow(),
            )
            session.add(demo_customer)
            await session.commit()

        # Demo products (if not already present)
        result = await session.execute(select(Product))
        existing_products = result.scalars().all()

        if not existing_products:
            products = [
                Product(
                    name="Mechanical Keyboard",
                    price=129.99,
                    stock=42,
                    created_at=datetime.utcnow(),
                ),
                Product(
                    name="Wireless Mouse",
                    price=59.99,
                    stock=100,
                    created_at=datetime.utcnow(),
                ),
                Product(
                    name="USB-C Hub",
                    price=49.99,
                    stock=75,
                    created_at=datetime.utcnow(),
                ),
            ]
            session.add_all(products)
            await session.commit()
