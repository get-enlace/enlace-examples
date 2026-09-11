# enlace-examples / fastapi

A FastAPI service implementing the [shared example contract](../CONTRACT.md) — E-commerce API with OAuth2 auth and carrier webhooks.

**Production reference implementation** using PostgreSQL (Neon recommended). The OpenAPI document is generated automatically by FastAPI from Pydantic schemas and route signatures — zero hand-written annotations.

## Features

- **PostgreSQL** (Neon recommended for dev/prod; `DATABASE_URL` required)
- **OAuth2 token endpoint** (`POST /oauth/token`) supporting RFC 6749 password + client_credentials grants
- **Three auth actors**: Customer (password grant) → Cart/Orders/Profile, Admin (client_credentials) → Product mgmt/Fulfillment, Carrier (static API key) → Delivery status webhook
- **Fixtures seeded on startup** (upsert-if-missing): demo customer `alice@example.com`, admin client `admin-service`, carrier key `carrier-demo-key`
- **Auto-generated OpenAPI** from Pydantic models, `/docs` for Swagger UI, `/enlace` for the Enlace canvas

## Setup

**Requires PostgreSQL** — Local Postgres, Neon free tier, or Render's Postgres all work.

### 1. Get a Postgres connection string

- **Local**: `postgresql://user:password@localhost/dbname`
- **Neon** (free): https://console.neon.tech → Create project → Copy connection string
- **Render**: Provisions Postgres with the web service

### 2. Install & run

```bash
export DATABASE_URL="postgresql://..."  # Your connection string

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.main
```

Or with auto-reload (dev only):

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

**PostgreSQL only** (async driver via `asyncpg`).

Set `DATABASE_URL` to any Postgres instance:
- Local: `postgresql://user:password@localhost/dbname`
- Neon (free): `postgresql://user:password@ep-xxx.us-east-1.neon.tech/dbname`
- Render: Provisioned automatically with the web service

Schema is created automatically on startup (upsert-if-missing fixtures too).

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

`requirements.txt` installs `enlace-fastapi` from test.pypi (development builds) with a fallback to the main PyPI index for dependencies. The latest dev build from test.pypi is pinned in requirements.txt.

To upgrade to a newer version:
1. Check test.pypi for the latest: https://test.pypi.org/project/enlace-fastapi/
2. Update the version pin in `requirements.txt`
3. `pip install -r requirements.txt --upgrade`

Once a production release is pushed to PyPI, swap the `--index-url` line to use only https://pypi.org/simple/

## Environment Variables

- `PORT` (default: `4000`)
- `DATABASE_URL` (default: `sqlite:///./fastapi.db`)
- `DEMO_CUSTOMER_EMAIL` (default: `alice@example.com`)
- `DEMO_CUSTOMER_PASSWORD` (default: `demo-password-123`)
- `ADMIN_CLIENT_ID` (default: `admin-service`)
- `ADMIN_CLIENT_SECRET` (default: `admin-service-secret`)
- `CARRIER_API_KEY` (default: `carrier-demo-key`)
