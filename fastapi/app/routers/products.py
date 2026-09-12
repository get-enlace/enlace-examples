"""Product resource endpoints - using SQLAlchemy ORM."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_admin_id
from ..errors import not_found
from ..models import Product
from ..schemas import ErrorResponse, Product as ProductSchema
from ..schemas import ProductRequest

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductSchema])
def list_products(db: Session = Depends(get_db)) -> list[ProductSchema]:
    """List all products (public)."""
    result = db.execute(select(Product).order_by(Product.id))
    products = result.scalars().all()
    return [
        ProductSchema(id=p.id, name=p.name, price=p.price, stock=p.stock)
        for p in products
    ]


@router.get("/products/{id}", response_model=ProductSchema)
def get_product(id: int, db: Session = Depends(get_db)) -> ProductSchema:
    """Get a specific product (public)."""
    result = db.execute(select(Product).where(Product.id == id))
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
def create_product(
    req: ProductRequest,
    _admin: bool = Depends(get_current_admin_id),
    db: Session = Depends(get_db),
) -> ProductSchema:
    """Create a product (admin only)."""
    product = Product(
        name=req.name,
        price=req.price,
        stock=req.stock,
        created_at=datetime.utcnow(),
    )
    db.add(product)
    db.flush()
    product_id = product.id
    db.commit()
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
def update_product(
    id: int,
    req: ProductRequest,
    _admin: bool = Depends(get_current_admin_id),
    db: Session = Depends(get_db),
) -> ProductSchema:
    """Update a product (admin only)."""
    result = db.execute(select(Product).where(Product.id == id))
    product = result.scalars().first()
    if not product:
        raise not_found("Product", id)

    product.name = req.name
    product.price = req.price
    product.stock = req.stock

    db.commit()

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
def delete_product(
    id: int,
    _admin: bool = Depends(get_current_admin_id),
    db: Session = Depends(get_db),
) -> None:
    """Delete a product (admin only)."""
    result = db.execute(select(Product).where(Product.id == id))
    product = result.scalars().first()
    if not product:
        raise not_found("Product", id)

    db.delete(product)
    db.commit()
