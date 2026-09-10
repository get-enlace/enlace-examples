"""Product resource endpoints.

- GET /products (public) — all products
- GET /products/{id} (public) — one product
- POST /products (admin only) — create a product
- PUT /products/{id} (admin only) — update a product
- DELETE /products/{id} (admin only) — delete a product
"""

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_admin_id
from ..errors import not_found
from ..schemas import ErrorResponse, Product, ProductRequest

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[Product])
async def list_products() -> list[Product]:
    """List all products (public)."""
    rows = await database.fetch_all(
        "SELECT id, name, price, stock FROM products ORDER BY id"
    )
    return [
        Product(id=r["id"], name=r["name"], price=r["price"], stock=r["stock"])
        for r in rows
    ]


@router.get("/products/{id}", response_model=Product)
async def get_product(id: int) -> Product:
    """Get a specific product (public)."""
    row = await database.fetch_one(
        "SELECT id, name, price, stock FROM products WHERE id = :id",
        values={"id": id},
    )
    if not row:
        raise not_found("Product", id)
    return Product(id=row["id"], name=row["name"], price=row["price"], stock=row["stock"])


@router.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def create_product(
    req: ProductRequest,
    _admin: bool = Depends(get_current_admin_id),
) -> Product:
    """Create a product (admin only)."""
    product_id = await database.execute(
        """INSERT INTO products (name, price, stock)
           VALUES (:name, :price, :stock)""",
        values={
            "name": req.name,
            "price": req.price,
            "stock": req.stock,
        },
    )
    return Product(id=product_id, name=req.name, price=req.price, stock=req.stock)


@router.put(
    "/products/{id}",
    response_model=Product,
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
) -> Product:
    """Update a product (admin only)."""
    existing = await database.fetch_one(
        "SELECT id FROM products WHERE id = :id",
        values={"id": id},
    )
    if not existing:
        raise not_found("Product", id)

    await database.execute(
        """UPDATE products SET name = :name, price = :price, stock = :stock
           WHERE id = :id""",
        values={
            "name": req.name,
            "price": req.price,
            "stock": req.stock,
            "id": id,
        },
    )

    return Product(id=id, name=req.name, price=req.price, stock=req.stock)


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
) -> None:
    """Delete a product (admin only)."""
    existing = await database.fetch_one(
        "SELECT id FROM products WHERE id = :id",
        values={"id": id},
    )
    if not existing:
        raise not_found("Product", id)

    await database.execute(
        "DELETE FROM products WHERE id = :id",
        values={"id": id},
    )
