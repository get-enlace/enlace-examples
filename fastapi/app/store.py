"""In-memory data store — see ../../CONTRACT.md. In-memory only, resets on
restart.

A dumb data store: existence checks and error shaping live in the routers,
matching how the express/nest examples structure it (nest's
`StoreService` plays the identical role here).
"""

from .schemas import Customer, Order, Product

ResourceKind = str  # "customer" | "product" | "order" — see next_id() below


class InMemoryStore:
    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}
        self.products: dict[int, Product] = {}
        self.orders: dict[int, Order] = {}
        self._next_ids = {"customer": 1, "product": 1, "order": 1}

    def next_id(self, resource: ResourceKind) -> int:
        id_ = self._next_ids[resource]
        self._next_ids[resource] += 1
        return id_


# One store for the process's lifetime, shared by every request via the
# get_store dependency below — FastAPI's own equivalent of injecting a
# singleton provider (e.g. nest's `@Injectable() StoreService`).
_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store
