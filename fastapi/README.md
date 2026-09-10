# enlace-examples / fastapi

A FastAPI service implementing the [shared example contract](../CONTRACT.md) — E-commerce API with OAuth2 auth and carrier webhooks. In-memory for dev, swappable to Postgres for production via `DATABASE_URL` env var.

The OpenAPI document is generated automatically by FastAPI from Pydantic schemas and route signatures — zero hand-written annotations.

## Features

- **SQLite by default** (zero external setup) + Postgres via `DATABASE_URL`
- **OAuth2 token endpoint** (`POST /oauth/token`) supporting RFC 6749 password + client_credentials grants
- **Three auth actors**: Customer (password grant) → Cart/Orders/Profile, Admin (client_credentials) → Product mgmt/Fulfillment, Carrier (static API key) → Delivery status webhook
- **Fixtures seeded on startup** (upsert-if-missing): demo customer `alice@example.com`, admin client `admin-service`, carrier key `carrier-demo-key`
- **Auto-generated OpenAPI** from Pydantic models, `/docs` for Swagger UI, `/enlace` for the Enlace canvas

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
```

Or, for auto-reload during development:

```bash
uvicorn app.main:app --reload --port 4000
```

Open:
- `http://localhost:4000/enlace` — Enlace canvas
- `http://localhost:4000/enlace/api/spec` — OpenAPI document (resolved by canvas)
- `http://localhost:4000/docs` — Swagger UI
- `http://localhost:4000/customers`, `/products`, `/orders`, etc. — API endpoints directly

## OAuth2 Token Endpoint

`POST /oauth/token` (excluded from OpenAPI spec) handles two grants:

**Password grant** (customer login):
```bash
curl -X POST http://localhost:4000/oauth/token \
  -d "grant_type=password&username=alice@example.com&password=demo-password-123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Response:
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "customer"
}
```

**Client credentials grant** (admin/service):
```bash
curl -X POST http://localhost:4000/oauth/token \
  -d "grant_type=client_credentials&client_id=admin-service&client_secret=admin-service-secret" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Both produce `Authorization: Bearer <token>` headers for subsequent API calls. Customer tokens are scoped to that customer's own resources; admin tokens get full visibility.

## Database

**Dev (default):** SQLite at `fastapi.db` (auto-created on first run).

**Production:** Set `DATABASE_URL` (e.g., `postgresql://user:password@localhost/enlace_demo`) to use Postgres. Schema is created automatically on startup (upsert-if-missing fixtures too).

Supported URLs:
- `sqlite:///./fastapi.db` (default, relative path)
- `sqlite:////tmp/enlace.db` (absolute path)
- `postgresql://user:pass@host/dbname`
- `postgresql+asyncpg://user:pass@host/dbname`

## Reference Demo Chain

See [CONTRACT.md](../../CONTRACT.md#reference-demo-chain) for the 8-step canvas workflow. In the Enlace UI:

1. Configure three credentials in the Credential Manager:
   - `customer`: oauth2_password, tokenUrl = `http://localhost:4000/oauth/token`, username = `alice@example.com`, password = `demo-password-123`
   - `admin`: oauth2_clientCredentials, same tokenUrl, client_id = `admin-service`, client_secret = `admin-service-secret`
   - `carrier`: apiKey, header `X-Carrier-Api-Key`, value = `carrier-demo-key`

2. Build the chain (8 steps, credential switches at steps 6 and 7):
   - Step 1: `GET /products` (no credential)
   - Step 2: `POST /carts` (attach `customer` credential)
   - Step 3: `POST /carts/{cartId}/items` (map product from step 1)
   - Step 4: `POST /carts/{cartId}/checkout` (maps order + payment from response)
   - Step 5: `POST /payments/{id}/confirm` (switch to `customer`, map payment.id from step 4)
   - Step 6: `POST /orders/{id}/fulfill` (switch to `admin` credential, map order.id from step 4)
   - Step 7: `PUT /shipments/{trackingNumber}/status` (switch to `carrier` credential, map trackingNumber from step 6)
   - Step 8: `GET /shipments/{trackingNumber}` (no credential, verify final state)

This demonstrates Enlace's core value: chaining across different API actors and mapping nested fields from compound responses.

## Picking up a newer `enlace-fastapi`

`requirements.txt` installs `enlace-fastapi` as an editable path dependency
(`-e ../../enlace-python/packages/enlace-fastapi`). Once it's published to PyPI, swap that for:

```
enlace-fastapi==<version>
```

## Environment Variables

- `PORT` (default: `4000`)
- `DATABASE_URL` (default: `sqlite:///./fastapi.db`)
- `DEMO_CUSTOMER_EMAIL` (default: `alice@example.com`)
- `DEMO_CUSTOMER_PASSWORD` (default: `demo-password-123`)
- `ADMIN_CLIENT_ID` (default: `admin-service`)
- `ADMIN_CLIENT_SECRET` (default: `admin-service-secret`)
- `CARRIER_API_KEY` (default: `carrier-demo-key`)
