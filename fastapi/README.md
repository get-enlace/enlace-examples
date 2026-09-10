# enlace-examples / fastapi

A minimal FastAPI service implementing the [shared example contract](../CONTRACT.md) — in-memory
`Customers`, `Products`, and `Orders` — wired up with
[`enlace-python`](../../enlace-python/packages/enlace-fastapi)'s `enlace-fastapi` package.

The OpenAPI document comes from FastAPI's own `app.openapi()`, built automatically from the
Pydantic schemas and routes under `app/`, not hand-written.

## Layout

```
app/
├── main.py              # app factory: wires routers, error handlers, and enlace() together
├── config.py             # Settings (currently just PORT)
├── schemas.py            # Pydantic request/response models for every resource
├── store.py              # in-memory data store, injected into routers via Depends
├── errors.py             # reshapes FastAPI's default error envelopes into CONTRACT.md's shape
└── routers/
    ├── customers.py
    ├── products.py
    └── orders.py
```

## Setup

`enlace-fastapi` isn't published anywhere yet, so this installs it from the sibling
`enlace-python` checkout instead of a registry:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
```

Or, for auto-reload during development (port must match `PORT`, default `4000` either way):

```bash
uvicorn app.main:app --reload --port 4000
```

Open `http://localhost:4000/enlace` for the canvas, or `http://localhost:4000/enlace/api/spec` to
see the OpenAPI document directly. `/customers`, `/products`, `/orders` (the sample API) are also
live. See [`CONTRACT.md`](../CONTRACT.md#reference-demo-chain) for a chain to try on the canvas.

## Picking up a real `enlace-fastapi` release

`requirements.txt` installs `enlace-fastapi` as an editable path dependency
(`-e ../../enlace-python/packages/enlace-fastapi`) — swap that line for a pinned
`enlace-fastapi==<version>` once it publishes to PyPI.
