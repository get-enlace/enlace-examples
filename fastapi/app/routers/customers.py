"""Customers resource — see ../../../CONTRACT.md. Independent CRUD; Orders
references this resource by id.
"""

from fastapi import APIRouter, Depends

from ..errors import not_found
from ..schemas import Customer, CustomerRequest, ErrorResponse
from ..store import InMemoryStore, get_store

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", operation_id="listCustomers", summary="List customers")
def list_customers(store: InMemoryStore = Depends(get_store)) -> list[Customer]:
    return list(store.customers.values())


@router.get(
    "/{id}",
    operation_id="getCustomer",
    summary="Fetch a customer by id",
    responses={404: {"model": ErrorResponse}},
)
def get_customer(id: int, store: InMemoryStore = Depends(get_store)) -> Customer:
    customer = store.customers.get(id)
    if customer is None:
        raise not_found("Customer", id)
    return customer


@router.post("", operation_id="createCustomer", summary="Create a customer", status_code=201)
def create_customer(body: CustomerRequest, store: InMemoryStore = Depends(get_store)) -> Customer:
    customer = Customer(id=store.next_id("customer"), **body.model_dump())
    store.customers[customer.id] = customer
    return customer


@router.put(
    "/{id}",
    operation_id="updateCustomer",
    summary="Update a customer",
    responses={404: {"model": ErrorResponse}},
)
def update_customer(id: int, body: CustomerRequest, store: InMemoryStore = Depends(get_store)) -> Customer:
    if id not in store.customers:
        raise not_found("Customer", id)
    customer = Customer(id=id, **body.model_dump())
    store.customers[id] = customer
    return customer


@router.delete(
    "/{id}",
    operation_id="deleteCustomer",
    summary="Delete a customer",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
def delete_customer(id: int, store: InMemoryStore = Depends(get_store)) -> None:
    if store.customers.pop(id, None) is None:
        raise not_found("Customer", id)
