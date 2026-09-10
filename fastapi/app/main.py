"""App factory — wires the routers, error handlers, and the Enlace adapter
together. See ../README.md for how to run this, and ../../CONTRACT.md for
the API it serves.
"""

from enlace_fastapi import enlace
from fastapi import FastAPI

from .config import settings
from .errors import register_error_handlers
from .routers import customers, orders, products


def create_app() -> FastAPI:
    app = FastAPI(
        title="Enlace Example API (FastAPI)",
        version="1.0.0",
        # Enlace's chain executor reads servers[0].url to know where to send
        # the actual HTTP requests — see ARCHITECTURE.md §3/§6. FastAPI
        # doesn't set this on its own; every other example here sets it
        # explicitly too (aspnetcore's AddServer, nest's .addServer(...)).
        servers=[{"url": f"http://localhost:{settings.port}"}],
    )

    register_error_handlers(app)

    app.include_router(customers.router)
    app.include_router(products.router)
    app.include_router(orders.router)

    # Mounted last: app.openapi() builds (and caches) the schema from the
    # routers registered above, so this needs to run after them — see
    # enlace-fastapi's own README for the same requirement.
    app.include_router(enlace(spec=app.openapi()), prefix="/enlace")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    print(f"Enlace example (FastAPI) running at http://localhost:{settings.port}")
    print(f"  Canvas:  http://localhost:{settings.port}/enlace")
    print(f"  Spec:    http://localhost:{settings.port}/enlace/api/spec")
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
