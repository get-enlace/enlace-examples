"""App factory — wires the routers, error handlers, database, and Enlace adapter together.

See ../README.md for how to run this, and ../../CONTRACT.md for the API it serves.
"""

from contextlib import asynccontextmanager

from enlace_fastapi import enlace
from fastapi import FastAPI

from .config import settings
from .db import close_db, init_db
from .errors import register_error_handlers
from .routers import auth, carts, customers, orders, payments, products, shipments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: initialize DB on startup, close on shutdown."""
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "See README.md for setup instructions."
        )
    print(f"Initializing database at {settings.database_url}...")
    init_db()
    print("Database initialized.")
    yield
    print("Closing database...")
    close_db()
    print("Database closed.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Enlace Example API (FastAPI)",
        version="2.0.0",
        description="E-commerce API with OAuth2 auth (password + client_credentials) and carrier webhook",
        lifespan=lifespan,
        # No `servers` entry on purpose — Enlace UI resolves the request base
        # URL against wherever the spec document itself was fetched from
        # (enlace's resolveBaseUrl, per the OpenAPI Server Object's own
        # default of `/` when `servers` is omitted), so this works unmodified
        # on Render, localhost, or anywhere else this app is deployed. An
        # earlier hardcoded `servers=[{"url": "https://enlace-fastapi.onrender.com"}]`
        # here was a workaround for a real gap in enlace, since fixed
        # there — see its git history for that fix if this ever needs
        # revisiting.
    )

    register_error_handlers(app)

    # Register routers
    app.include_router(auth.router)
    app.include_router(customers.router)
    app.include_router(products.router)
    app.include_router(carts.router)
    app.include_router(orders.router)
    app.include_router(payments.router)
    app.include_router(shipments.router)

    # Mounted last: app.openapi() builds (and caches) the schema from the
    # routers registered above. Enlace's own swagger UI is mounted at /enlace.
    app.include_router(enlace(spec=app.openapi()), prefix="/enlace")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    print(f"Enlace example (FastAPI) running at http://localhost:{settings.port}")
    print(f"  Canvas:  http://localhost:{settings.port}/enlace")
    print(f"  Spec:    http://localhost:{settings.port}/enlace/api/spec")
    print(f"  Docs:    http://localhost:{settings.port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
