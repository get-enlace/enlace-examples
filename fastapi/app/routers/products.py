"""Products resource — see ../../../CONTRACT.md. Independent CRUD; Orders
references this resource by id.
"""

from fastapi import APIRouter, Depends

from ..errors import not_found
from ..schemas import ErrorResponse, Product, ProductRequest
from ..store import InMemoryStore, get_store

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", operation_id="listProducts", summary="List products")
def list_products(store: InMemoryStore = Depends(get_store)) -> list[Product]:
    return list(store.products.values())


@router.get(
    "/{id}",
    operation_id="getProduct",
    summary="Fetch a product by id",
    responses={404: {"model": ErrorResponse}},
)
def get_product(id: int, store: InMemoryStore = Depends(get_store)) -> Product:
    product = store.products.get(id)
    if product is None:
        raise not_found("Product", id)
    return product


@router.post("", operation_id="createProduct", summary="Create a product", status_code=201)
def create_product(body: ProductRequest, store: InMemoryStore = Depends(get_store)) -> Product:
    product = Product(id=store.next_id("product"), **body.model_dump())
    store.products[product.id] = product
    return product


@router.put(
    "/{id}",
    operation_id="updateProduct",
    summary="Update a product",
    responses={404: {"model": ErrorResponse}},
)
def update_product(id: int, body: ProductRequest, store: InMemoryStore = Depends(get_store)) -> Product:
    if id not in store.products:
        raise not_found("Product", id)
    product = Product(id=id, **body.model_dump())
    store.products[id] = product
    return product


@router.delete(
    "/{id}",
    operation_id="deleteProduct",
    summary="Delete a product",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
def delete_product(id: int, store: InMemoryStore = Depends(get_store)) -> None:
    if store.products.pop(id, None) is None:
        raise not_found("Product", id)
