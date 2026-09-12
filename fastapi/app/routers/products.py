"""Product resource endpoints - using SQLAlchemy ORM."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_admin_id
from ..errors import not_found
from ..models import Product
from ..schemas import ErrorResponse, Product as ProductSchema
from ..schemas import ProductRequest

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductSchema])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[ProductSchema]:
    """List all products (public)."""
    result = await db.execute(select(Product).order_by(Product.id))
    products = result.scalars().all()
    return [
        ProductSchema(id=p.id, name=p.name, price=p.price, stock=p.stock)
        for p in products
    ]


@router.get("/products/{id}", response_model=ProductSchema)
async def get_product(id: int, db: AsyncSession = Depends(get_db)) -> ProductSchema:
    """Get a specific product (public)."""
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalars().first()
    if not product:
        raise not_found("Product", id)
    return ProductSchema(id=product.id, name=product.name, price=product.price, stock=product.stock)


@router.post(
    "/products",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def create_product(
    req: ProductRequest,
    _admin: bool = Depends(get_current_admin_id),
    db: AsyncSession = Depends(get_db),
) -> ProductSchema:
    """Create a product (admin only)."""
    product = Product(
        name=req.name,
        price=req.price,
        stock=req.stock,
        created_at=datetime.utcnow(),
    )
    db.add(product)
    await db.flush()
    product_id = product.id
    return ProductSchema(id=product_id, name=req.name, price=req.price, stock=req.stock)


@router.put(
    "/products/{id}",
    response_model=ProductSchema,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def update_product(
    id: int,
    req: ProductRequest,
    _admin: bool = Depends(get_current_admin_id),
    db: AsyncSession = Depends(get_db),
) -> ProductSchema:
    """Update a product (admin only)."""
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalars().first()
    if not product:
        raise not_found("Product", id)

    product.name = req.name
    product.price = req.price
    product.stock = req.stock

    await db.commit()

    return ProductSchema(id=product.id, name=product.name, price=product.price, stock=product.stock)


@router.delete(
    "/products/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def delete_product(
    id: int,
    _admin: bool = Depends(get_current_admin_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a product (admin only)."""
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalars().first()
    if not product:
        raise not_found("Product", id)

    await db.delete(product)
    await db.commit()
