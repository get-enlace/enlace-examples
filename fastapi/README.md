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

## Live Demo Instance

🚀 **Live at:** https://enlace-fastapi.onrender.com/enlace/

- **Canvas:** https://enlace-fastapi.onrender.com/enlace/
- **API Docs:** https://enlace-fastapi.onrender.com/docs
- **OpenAPI Spec:** https://enlace-fastapi.onrender.com/enlace/api/spec

Fixtures seeded on startup:
- Demo customer: `alice@example.com` / `demo-password-123`
- Admin client: `admin-service` / `admin-service-secret`
- Carrier API key: `carrier-demo-key`

## Reference Demo Chain

See [CONTRACT.md](../../CONTRACT.md#reference-demo-chain) for the complete 8-step workflow. Follow these steps in the Enlace Canvas at the live link above:

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

## Testing the Live Demo

### Step 1: Open the Canvas

Go to: https://enlace-fastapi.onrender.com/enlace/

### Step 2: Configure Credentials (Credential Manager)

1. Click **Credentials** (top-right icon or sidebar)
2. Create three credentials:

   **Credential 1 — Customer (password grant)**
   - Name: `customer`
   - Type: `oauth2_password`
   - Token URL: `https://enlace-fastapi.onrender.com/oauth/token`
   - Username: `alice@example.com`
   - Password: `demo-password-123`

   **Credential 2 — Admin (client credentials grant)**
   - Name: `admin`
   - Type: `oauth2_clientCredentials`
   - Token URL: `https://enlace-fastapi.onrender.com/oauth/token`
   - Client ID: `admin-service`
   - Client Secret: `admin-service-secret`
   - Client Auth Method: `body` (or `basic`)

   **Credential 3 — Carrier (API key)**
   - Name: `carrier`
   - Type: `apiKey`
   - Parameter Name: `X-Carrier-Api-Key`
   - Location: `header`
   - Key: `carrier-demo-key`

### Step 3: Build the 8-Step Chain

On the canvas, create nodes in this order, attaching credentials as noted:

1. **GET /products** (no credential)
   - Capture: `id` from first product

2. **POST /carts** (attach `customer` credential)
   - Capture: cart `id`

3. **POST /carts/{cartId}/items** (attach `customer` credential)
   - Path param `cartId`: map from step 2's `id`
   - Body: `{ "productId": <from step 1>, "quantity": 1 }`
   - Capture: nothing (or verify items array)

4. **POST /carts/{cartId}/checkout** (attach `customer` credential)
   - Path param `cartId`: map from step 2's `id`
   - **KEY MAPPING:** Capture BOTH:
     - `order.id` (for step 6)
     - `payment.id` (for step 5)
   - This is a compound response mapping!

5. **POST /payments/{id}/confirm** (attach `customer` credential)
   - Path param `id`: map from step 4's `payment.id`
   - Body: `{ "method": "card" }`
   - Capture: nothing (order cascaded to "paid")

6. **POST /orders/{id}/fulfill** (attach `admin` credential)
   - **Switch credential to `admin` here**
   - Path param `id`: map from step 4's `order.id`
   - Capture: shipment `trackingNumber`

7. **PUT /shipments/{trackingNumber}/status** (attach `carrier` credential)
   - **Switch credential to `carrier` here**
   - Path param `trackingNumber`: map from step 6's `trackingNumber`
   - Body: `{ "status": "delivered" }`

8. **GET /shipments/{trackingNumber}** (no credential)
   - Path param `trackingNumber`: map from step 7
   - Verify: `status` is now `"delivered"`

### Step 4: Run the Chain

1. Click **Run** (play icon)
2. Watch each step execute in sequence
3. Each step shows request/response in the debug pane
4. Final step shows shipment in "delivered" state ✅

### Expected Outcomes

- ✅ All 8 steps succeed (green)
- ✅ Orders progress: `pending_payment` → `paid` → `shipped` → `delivered`
- ✅ Nested mapping works (order.id and payment.id from one response)
- ✅ Credential switches work (customer → admin → carrier)
- ✅ Status cascade works (payment confirm cascades order to "paid", fulfill creates shipment & cascades to "shipped", delivery updates cascade to "delivered")

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
