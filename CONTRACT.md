# Shared example API contract

Every per-framework example under this repo (`aspnetcore/`, `express/`, `nest/`, `java/`, `fastapi/`, ...) implements
**this exact API** — same resources, same fields, same endpoints, same auth, same error shape. The
point is that a chain built against one language's example works unmodified against any
other's: it's the same demo, just served by a different adapter.

Domain: a small e-commerce API — register/log in, browse a public product catalog, build a
cart, check out (creating an `Order` + `Payment`), confirm payment, have an internal
admin/service credential fulfill the order, then have the shipping carrier post a delivery
update. Three independent, realistic auth actors and six interconnected resources — enough
for a chain that crosses credential boundaries twice, not just a flat CRUD.

## Conventions

- JSON only, camelCase field names.
- IDs: integers, server-assigned, auto-incrementing from 1 (per resource type). Never accepted on create.
- Timestamps: ISO 8601, UTC (e.g. `"2026-08-23T12:00:00Z"`).
- Storage: a real database, not in-memory — SQLite by default (zero external setup for local
  dev), swappable for Postgres via a `DATABASE_URL` env var (used by the one publicly deployed
  instance, on Neon). Data survives restarts; only the fixtures described under **Auth** are
  guaranteed present (seeding is an upsert-if-missing on startup, never a wipe).
- `POST` (create) → `201` + the full created resource (including server-assigned fields).
- `POST` (action, e.g. checkout/confirm/fulfill/cancel) → `200` + the full updated/created resource(s).
- `PUT` → `200` + the full updated resource.
- `DELETE` → `204`, empty body.
- `GET` (collection) → `200` + a bare JSON array, no pagination envelope.
- Not found (including "not yours") → `404` + `{ "error": "<message>" }`.
- Invalid input (including a referenced id that doesn't exist) → `400` + `{ "error": "<message>" }`.
- Valid state, wrong transition (e.g. confirming an already-confirmed payment) → `409` + `{ "error": "<message>" }`.
- Missing/invalid credential → `401` + `{ "error": "<message>" }`.
- Valid credential, wrong actor for this endpoint (e.g. a customer token on an admin-only
  route) → `403` + `{ "error": "<message>" }`.
- **Exception:** `POST /oauth/token` follows RFC 6749's own request/response shape instead of
  the above — see **Auth**. It's the one endpoint a real OAuth2 client (including Enlace's own
  credential engine) talks to directly, so it has to look like a real token endpoint.

## Auth

Three independent actors, none of which can act as either of the others:

| Actor | Mechanism | Header on API calls | Scope |
|---|---|---|---|
| Customer | OAuth2 **password** grant | `Authorization: Bearer <token>` | that one customer's own cart/orders/profile |
| Admin/internal service | OAuth2 **client_credentials** grant | `Authorization: Bearer <token>` | catalog management, fulfillment, full order/customer visibility |
| Shipping carrier | static API key | `X-Carrier-Api-Key: <key>` | posting delivery-status updates only |

Customer and admin tokens are byte-for-byte the same *kind* of header
(`Authorization: Bearer ...`) — the server tells them apart by the scope recorded against the
opaque token itself, not by header shape. That's deliberate: it's a realistic case (same
header, different token audience) and it means `GET /orders` genuinely needs to check *which*
kind of bearer token it got, not just whether one was present.

### `POST /oauth/token`

One endpoint, both grants, dispatched on the `grant_type` form field — `Content-Type:
application/x-www-form-urlencoded` request, JSON response. This is the exact contract
`enlace-ui`'s credential engine expects (`packages/core/src/engine/credentials.ts`), since it
calls this URL itself, generically, whenever a node uses an `oauth2_password` or
`oauth2_clientCredentials` credential.

**`grant_type=password`** (customer): body `username` (the customer's email), `password`.
Public client — no `client_id`/`client_secret` expected or checked.

**`grant_type=client_credentials`** (admin/service): `client_id`/`client_secret` accepted
*either* as HTTP Basic auth on this request (`client_secret_basic`) *or* as `client_id`/
`client_secret` form fields (`client_secret_post`) — accept both, since which one a given
Enlace credential uses is a per-credential UI choice, not something this API controls.

Success (either grant) → `200`:
```json
{ "access_token": "...", "token_type": "Bearer", "expires_in": 3600, "scope": "customer" }
```
(`scope` is `"customer"` or `"admin"`.)

Failure → `400` + RFC 6749's error shape, e.g. `{ "error": "invalid_grant", "error_description": "..." }`
(`invalid_request` for a missing field, `unsupported_grant_type` for anything but the two
above, `invalid_grant` for wrong credentials).

### Fixtures (ensured present on every startup — upsert, never a wipe)

So the reference chain never requires a register step first, and so restarting a persistent
store doesn't touch data created since:

- One demo customer — `alice@example.com` / `demo-password-123` — usable immediately with
  `grant_type=password`.
- One admin OAuth2 client — `client_id=admin-service`, `client_secret=admin-service-secret` —
  overridable via `ADMIN_CLIENT_ID`/`ADMIN_CLIENT_SECRET` env vars.
- One carrier API key — `carrier-demo-key` — overridable via `CARRIER_API_KEY` env var.

`POST /auth/register` still works normally (`{ "name", "email", "password" }` → `201`
`Customer`, `400` if the email's taken) for anyone who wants their own customer instead of the
seeded one. Passwords are hashed at rest and never appear in any response.

## Resources

### Customer

```json
{ "id": 1, "name": "Ada Lovelace", "email": "ada@example.com" }
```

Updatable via `PUT /customers/me` (`{ "name": string, "email": string }`).

### Product

```json
{ "id": 1, "name": "Mechanical Keyboard", "price": 129.99, "stock": 42 }
```

`POST`/`PUT` body: `{ "name": string, "price": number, "stock": integer }`. Admin-managed;
`stock` is descriptive only — not decremented by orders.

### Cart

```json
{
  "id": 1,
  "customerId": 1,
  "items": [ { "productId": 1, "quantity": 2 } ],
  "createdAt": "2026-08-23T12:00:00Z"
}
```

Created empty via `POST /carts`. Adding an already-present `productId` increments its
quantity rather than duplicating the line. `400` if `productId` doesn't exist. Once checked
out, a cart is closed — a second checkout attempt on it is `409`.

### Order

References the `Customer` and `Cart` that created it, and the `Product`s in its `items`.
`unitPrice`/`total` are computed from each product's *current* price at checkout time —
response-only fields, deliberately not client-supplied, to give the canvas something worth
mapping from a response into a later step.

```json
{
  "id": 1,
  "customerId": 1,
  "cartId": 1,
  "items": [ { "productId": 1, "quantity": 2, "unitPrice": 129.99 } ],
  "total": 259.98,
  "status": "pending_payment",
  "createdAt": "2026-08-23T12:00:00Z"
}
```

`status` is one of `pending_payment | paid | shipped | delivered | cancelled`. Valid
transitions only — anything else is `409`:

```
pending_payment --confirm payment--> paid --fulfill--> shipped --carrier delivers--> delivered
pending_payment --cancel--------------------------------------------------------> cancelled
```

### Payment

Created alongside its `Order` at checkout, `amount` fixed to the order's `total`.

```json
{
  "id": 1,
  "orderId": 1,
  "amount": 259.98,
  "method": null,
  "status": "pending",
  "confirmedAt": null
}
```

`POST /payments/{id}/confirm` body: `{ "method": "card" | "paypal" }` → sets `method`,
`status: "succeeded"`, `confirmedAt`, and cascades the parent `Order` to `paid`. `409` if the
payment isn't `pending`.

### Shipment

Created by `POST /orders/{id}/fulfill` (admin/service only) once an order is `paid`.

```json
{
  "id": 1,
  "orderId": 1,
  "trackingNumber": "TRK-A1B2C3",
  "carrier": "DemoShip Express",
  "status": "in_transit",
  "createdAt": "2026-08-23T12:00:00Z"
}
```

`PUT /shipments/{trackingNumber}/status` (**carrier API key** — the one endpoint neither the
customer nor the admin/service credential can call) body: `{ "status": "delivered" }` →
cascades the parent `Order` to `delivered`. `409` if the shipment isn't `in_transit`.

## Endpoints

```
Actor            Method  Path                              Notes
—                POST    /auth/register                    { name, email, password } -> 201 Customer
—                POST    /oauth/token                       grant_type=password | client_credentials — see Auth

—                GET     /products
—                GET     /products/{id}
Admin            POST    /products
Admin            PUT     /products/{id}
Admin            DELETE  /products/{id}

Admin            GET     /customers                        all customers
Admin            GET     /customers/{id}
Customer         GET     /customers/me
Customer         PUT     /customers/me

Customer         POST    /carts
Customer         GET     /carts/{cartId}
Customer         POST    /carts/{cartId}/items              { productId, quantity }
Customer         DELETE  /carts/{cartId}/items/{productId}
Customer         POST    /carts/{cartId}/checkout            -> 201 { order: Order, payment: Payment }

Customer         GET     /payments/{id}
Customer         POST    /payments/{id}/confirm             { method } -> confirms + cascades order to paid

Customer | Admin GET     /orders                            customer: own only | admin: all
Customer | Admin GET     /orders/{id}                       customer: own only (404 if not yours) | admin: any
Customer         POST    /orders/{id}/cancel                 only from pending_payment
Admin            POST    /orders/{id}/fulfill                only from paid -> creates Shipment, order -> shipped

—                GET     /shipments/{trackingNumber}         public: tracking number is itself the secret
Carrier          PUT     /shipments/{trackingNumber}/status  { status: "delivered" } -> cascades order
```

## Reference demo chain

The workflow every language's README should walk through on the Enlace canvas. Unlike the
old no-auth version, most of the "auth work" happens once, outside the chain itself —
configuring credentials, not chaining a login call:

**Setup (once, in Enlace's credential manager — not chain nodes):**
- A `customer` credential: `oauth2_password`, `tokenUrl` = this API's `/oauth/token`,
  `username`/`password` = the seeded demo customer (or your own, after registering).
- An `admin` credential: `oauth2_clientCredentials`, same `tokenUrl`, `clientId`/`clientSecret`
  = the seeded admin client.
- A `carrier` credential: `apiKey`, header `X-Carrier-Api-Key`, value = the seeded carrier key.

**Chain (attach `customer` to nodes 1–5, `admin` to node 6, `carrier` to node 7):**

1. `GET /products` — pick a product's `id`
2. `POST /carts` — capture the new cart's `id`
3. `POST /carts/{cartId}/items` with `productId` mapped from step 1
4. `POST /carts/{cartId}/checkout` — capture `order.id` and `payment.id` (a nested-field
   mapping out of one compound response, into two different later steps)
5. `POST /payments/{id}/confirm` with `id` mapped from step 4's `payment.id`, body
   `{ "method": "card" }` — the order is now `paid`
6. `POST /orders/{id}/fulfill` with `id` mapped from step 4's `order.id` — **credential
   switches to `admin` here** — capture the new shipment's `trackingNumber`
7. `PUT /shipments/{trackingNumber}/status` with `trackingNumber` mapped from step 6, body
   `{ "status": "delivered" }` — **credential switches to `carrier` here**
8. `GET /shipments/{trackingNumber}` (no credential) — verify `status: "delivered"`

Eight chained steps, six resources, two credential switches mid-chain across three genuinely
different auth mechanisms, and a nested-response mapping — a real showcase of per-node auth
handling, not just chained IDs.
