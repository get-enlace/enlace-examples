# Shared example API contract

Every per-framework example under this repo (`aspnetcore/`, `express/`, `nest/`, `java/`, `fastapi/`, ...) implements
**this exact API** — same resources, same fields, same endpoints, same error shape. The
point is that a chain built against one language's example works unmodified against any
other's: it's the same demo, just served by a different adapter.

Domain: a minimal e-commerce API — `Customers` and `Products` are independent CRUDs,
`Orders` references both, which gives a workflow with real cross-node data mapping to
demo (not just a single flat CRUD).

## Conventions

- JSON only, camelCase field names.
- IDs: integers, server-assigned, auto-incrementing from 1. Never accepted on create.
- Timestamps: ISO 8601, UTC (e.g. `"2026-08-23T12:00:00Z"`).
- Storage: in-memory, per running instance — resets on restart. No persistence, no auth.
- `POST` → `201` + the full created resource (including server-assigned fields).
- `PUT` → `200` + the full updated resource.
- `DELETE` → `204`, empty body.
- `GET` (collection) → `200` + a bare JSON array, no pagination envelope.
- Not found → `404` + `{ "error": "<message>" }`.
- Invalid input (including a referenced id that doesn't exist, e.g. an order's
  `customerId`) → `400` + `{ "error": "<message>" }`.

## Resources

### Customer

```json
{ "id": 1, "name": "Ada Lovelace", "email": "ada@example.com" }
```

`POST`/`PUT` body: `{ "name": string, "email": string }`

### Product

```json
{ "id": 1, "name": "Mechanical Keyboard", "price": 129.99, "stock": 42 }
```

`POST`/`PUT` body: `{ "name": string, "price": number, "stock": integer }`

### Order

References a `Customer` and one or more `Product`s. `unitPrice` and `total` are
server-computed from each product's *current* price at creation time — deliberately
response-only fields the client didn't send, to give the canvas something worth mapping
from a response into a later step.

```json
{
  "id": 1,
  "customerId": 1,
  "status": "pending",
  "items": [
    { "productId": 1, "quantity": 2, "unitPrice": 129.99 }
  ],
  "total": 259.98,
  "createdAt": "2026-08-23T12:00:00Z"
}
```

`POST` body: `{ "customerId": integer, "items": [{ "productId": integer, "quantity": integer }] }`
— `400` if `customerId` or any `productId` doesn't exist.

`status` is one of `pending | paid | shipped | cancelled` (default `pending` on create).
No transition validation — any of the four values is accepted.

## Endpoints

```
GET    /customers
GET    /customers/{id}
POST   /customers
PUT    /customers/{id}
DELETE /customers/{id}

GET    /products
GET    /products/{id}
POST   /products
PUT    /products/{id}
DELETE /products/{id}

GET    /orders
GET    /orders/{id}
POST   /orders
PUT    /orders/{id}/status     body: { "status": string }
DELETE /orders/{id}
```

## Reference demo chain

The workflow every language's README should walk through on the Enlace canvas:

1. `POST /customers` — capture the new customer's `id`
2. `POST /products` (×2, e.g. keyboard + mouse) — capture both `id`s
3. `POST /orders` with `customerId` mapped from step 1 and `items[].productId` mapped
   from step 2 — capture the order's `id` and see the server-computed `total`
4. `PUT /orders/{id}/status` with `id` mapped from step 3, body `{ "status": "paid" }`
5. `GET /orders/{id}` — verify the status change

Five chained steps across three resources, with two independent branches (customer,
products) feeding into a third — enough to be a real demo without being a maze.
