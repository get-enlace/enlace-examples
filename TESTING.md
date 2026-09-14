# Testing the Enlace Examples Canvas Chain

**Live Demo:** https://enlace-fastapi.onrender.com/enlace/ (FastAPI example on Render)

**Note:** This guide uses the FastAPI reference implementation, which includes full authentication (three security schemes: Customer JWT, Admin JWT, Carrier API Key). The other language examples (Express, Nest, ASP.NET Core, Java) currently implement only the basic CRUD contract and lack the auth layer — they're suitable for chaining basic operations but not the full 8-step workflow described here.

This guide walks through the complete 8-step reference chain that demonstrates Enlace's core capabilities:
- Multi-step chaining with data mapping
- Credential switching (3 different auth actors)
- Nested field mapping from compound responses
- Status cascading and state transitions

## Prerequisites

- Browser (Chrome, Firefox, Safari, Edge)
- Access to https://enlace-fastapi.onrender.com/enlace/
- No local setup required

## Part 1: Set Up Credentials in Enlace

You need **three credentials** for this chain:
- **Customer JWT** (password grant) — for cart and order operations
- **Admin JWT** (client credentials grant) — for fulfillment (admin operation)
- **API Key** (carrier) — for delivery status updates

The OpenAPI spec declares three distinct security schemes. Enlace will show all three.

### Step 1A: Generate Tokens via curl (Manual Approach)

First, get the actual tokens you'll use:

**Customer Token:**
```bash
curl -X POST https://enlace-fastapi.onrender.com/oauth/token \
  -d "grant_type=password&username=alice@example.com&password=demo-password-123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```
Response:
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "customer"
}
```
Copy the `access_token` value.

**Admin Token:**
```bash
curl -X POST https://enlace-fastapi.onrender.com/oauth/token \
  -d "grant_type=client_credentials&client_id=admin-service&client_secret=admin-service-secret" \
  -H "Content-Type: application/x-www-form-urlencoded"
```
Response:
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "admin"
}
```
Copy the `access_token` value.

### Step 1B: Configure Credentials in Enlace (Manual Token Approach)

1. Go to **https://enlace-fastapi.onrender.com/enlace/**
2. Click **Credentials** (top-right or sidebar)
3. Enlace shows three credential types. Create three credentials:

   **Credential 1: Customer**
   - Type: "Customer JWT" (HTTPBearer, from OpenAPI)
   - Name: `customer` (optional, for your reference)
   - Token: `<paste the access_token from curl above>`

   **Credential 2: Admin**
   - Type: "Admin JWT" (HTTPBearer, from OpenAPI)
   - Name: `admin` (optional, for your reference)
   - Token: `<paste the access_token from curl above>`

   **Credential 3: Carrier**
   - Type: "X-Carrier-Api-Key" (APIKeyHeader, from OpenAPI)
   - Name: `carrier` (optional, for your reference)
   - Key: `carrier-demo-key`

When you attach these credentials to nodes in the chain, Enlace will use the tokens you provided.

### Step 1C (Alternative, Recommended): Let Enlace Auto-Generate Tokens

Instead of manually generating and pasting tokens, reconfigure the credentials to let Enlace handle token generation automatically:

1. Go to **https://enlace-fastapi.onrender.com/enlace/**
2. Click **Credentials**
3. You should see the three credentials from Step 1B. Modify them:

   **Modify Credential 1: Customer**
   - Click the "customer" credential to edit
   - Change from: "Token: `<token>`"
   - Change to:
     - Type: "Customer JWT" (HTTPBearer)
     - Grant Type: `password` (Enlace will auto-generate)
     - Token URL: `https://enlace-fastapi.onrender.com/oauth/token`
     - Username: `alice@example.com`
     - Password: `demo-password-123`

   **Modify Credential 2: Admin**
   - Click the "admin" credential to edit
   - Change from: "Token: `<token>`"
   - Change to:
     - Type: "Admin JWT" (HTTPBearer)
     - Grant Type: `client_credentials` (Enlace will auto-generate)
     - Token URL: `https://enlace-fastapi.onrender.com/oauth/token`
     - Client ID: `admin-service`
     - Client Secret: `admin-service-secret`

   **Keep Credential 3: Carrier**
   - "X-Carrier-Api-Key" already uses the API key (no OAuth2 auto-generation available)
   - Leave as-is with `carrier-demo-key`

When you attach the "Customer JWT" or "Admin JWT" credentials to nodes, **Enlace automatically requests a fresh token** using the configured grant type, then attaches it as the Bearer token. No manual token generation or refresh needed. This approach is more practical for real workflows since tokens don't expire mid-chain.



## Part 2: Build the 8-Step Chain

On the canvas, create these operations in order. Data flows left-to-right or top-to-bottom depending on your layout.

### Step 1: Get Products (No Auth)

**Operation:** `GET /products`

**Configuration:**
- No credential needed (public endpoint)

**Capture for next steps:**
- Hover over the response and note the first product's `id` (usually `1`)

### Step 2: Create Cart (Customer Auth)

**Operation:** `POST /carts`

**Configuration:**
- Credential: Enlace will suggest `customer_oauth` (auto-discovered from spec)
- Body: (empty, no request body needed)

**Note:** Enlace shows which credential(s) this endpoint requires in a hint or badge.

**Capture for next steps:**
- Response field: `id` (the cart ID)

### Step 3: Add Item to Cart (Customer Auth)

**Operation:** `POST /carts/{cartId}/items`

**Configuration:**
- Credential: Select `customer`
- Path parameter `cartId`: **Map from Step 2** → select `id`
- Body:
  ```json
  {
    "productId": 1,
    "quantity": 1
  }
  ```
  Or map `productId` from Step 1's product `id` if you prefer.

**Capture for next steps:**
- Nothing specific; this just adds the item.

### Step 4: Checkout (Customer Auth) ⭐ **Nested Mapping**

**Operation:** `POST /carts/{cartId}/checkout`

**Configuration:**
- Credential: Select `customer`
- Path parameter `cartId`: **Map from Step 2** → select `id`
- Body: (empty)

**Capture for next steps (THIS IS KEY):**
- Response contains TWO objects we need:
  - `order.id` → Capture this for Step 6
  - `payment.id` → Capture this for Step 5
- This is a nested-field mapping: one response, two destinations

### Step 5: Confirm Payment (Customer Auth)

**Operation:** `POST /payments/{id}/confirm`

**Configuration:**
- Credential: Select `customer`
- Path parameter `id`: **Map from Step 4** → select `payment` → select `id`
  (This is nested mapping: `response.payment.id`)
- Body:
  ```json
  {
    "method": "card"
  }
  ```

**Result:**
- Payment status: `pending` → `succeeded`
- Order status cascades from `pending_payment` → `paid`

### Step 6: Fulfill Order (Admin Auth) ⭐ **First Credential Switch**

**Operation:** `POST /orders/{id}/fulfill`

**Configuration:**
- **Credential: Enlace will suggest `admin_oauth`** ← Enlace shows this requires admin (auto-discovered)
- Path parameter `id`: **Map from Step 4** → select `order` → select `id`
- Body: (empty)

**Note:** This endpoint requires a different credential than the previous steps. Enlace will show a warning/hint if you try to use the wrong credential.

**Capture for next steps:**
- Response field: `trackingNumber` (the shipment tracking number)

**Result:**
- Shipment created with status `in_transit`
- Order status cascades from `paid` → `shipped`

### Step 7: Update Shipment Status (Carrier Auth) ⭐ **Second Credential Switch**

**Operation:** `PUT /shipments/{trackingNumber}/status`

**Configuration:**
- **Credential: Enlace will suggest `carrier_api_key`** ← Third distinct auth actor (auto-discovered)
- Path parameter `trackingNumber`: **Map from Step 6** → select `trackingNumber`
- Body:
  ```json
  {
    "status": "delivered"
  }
  ```

**Note:** This is the third different credential type in the chain. Enlace's auto-discovery makes it clear which credential each endpoint needs.

**Result:**
- Order status cascades from `shipped` → `delivered`
- Shipment status becomes `delivered`

### Step 8: Verify Shipment (No Auth, Public)

**Operation:** `GET /shipments/{trackingNumber}`

**Configuration:**
- No credential needed (tracking number is public)
- Path parameter `trackingNumber`: **Map from Step 7** → select `trackingNumber`

**Verify:**
- Response shows:
  - `status: "delivered"` ✅
  - `trackingNumber` matches
  - `order.id` matches the order from Step 4

## Part 3: Run the Chain

1. Click the **Run** button (play icon, center-top or prominent button)
2. Watch the execution:
   - Each step lights up as it runs
   - Debug pane shows request/response for each step
   - Green = success, Red = failure
3. All 8 steps should complete in a few seconds

## Expected Results

### Success Indicators ✅

- [ ] Step 1: Returns array of 3+ products
- [ ] Step 2: Returns cart with `id` and empty `items` array
- [ ] Step 3: Returns cart with 1 item in `items` array
- [ ] Step 4: Returns compound object with both `order` and `payment`
  - `order.status: "pending_payment"`
  - `payment.status: "pending"`
- [ ] Step 5: Payment confirms
  - `payment.status: "succeeded"`
  - Order status cascades to `paid`
- [ ] Step 6: Shipment created (fulfillment succeeds)
  - `shipment.status: "in_transit"`
  - Order status cascades to `shipped`
- [ ] Step 7: Shipment updated
  - `shipment.status: "delivered"`
  - Order status cascades to `delivered`
- [ ] Step 8: Shipment verified
  - `status: "delivered"` ✅

### What This Demonstrates

| Feature | Steps | Why It Matters |
|---------|-------|---|
| **Chaining** | All 8 | Multiple calls in sequence, each output feeds into next input |
| **Data mapping** | 2→3, 2→4, 4→5, 4→6, 6→7, 7→8 | Extract fields from responses and map them to request paths/bodies |
| **Nested mapping** | Step 4 → Steps 5 & 6 | One response contains multiple fields used in different downstream steps |
| **Credential switching** | Step 5→6, Step 6→7 | Different auth actors execute different operations (customer → admin → carrier) |
| **Status cascading** | Steps 5, 6, 7 | Server state changes automatically based on previous operations |
| **Multi-actor workflow** | Full chain | Real-world scenario: customer places order, admin fulfills, carrier delivers |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Step fails with 401 | Credential is missing or invalid. Re-check credential name and values. |
| Step fails with 403 | Wrong credential type for this endpoint (e.g., customer token on admin-only endpoint). Switch credentials. |
| Step fails with 404 | Path parameter not mapped, or mapped value doesn't exist. Check the "Map from..." selector. |
| Mapping shows as "unmapped" | Scroll down to see the mapping options, or try a different field name. |
| Can't find nested field | In the "Map from..." modal, use the JSONPath filter to find `payment.id` or `order.id`. |
| Order status didn't cascade | This is automatic; check the response of the triggering step (confirm payment should cascade to paid). |

## Next Steps

Once you've run the chain once, try:

1. **Clear and rerun:** Clear all step results and re-execute with the same chain
2. **Modify quantities:** Change step 3's quantity to order 2 or 3 items
3. **Use a different product:** Map step 1's product ID to step 3 instead of hardcoding 1
4. **Export the chain:** Save the workflow (if Enlace supports export) and share it

## Reference

See [`CONTRACT.md`](CONTRACT.md#reference-demo-chain) for the formal specification of this chain.

---

**Questions?** Check the Enlace UI documentation or open the browser's developer console to see network requests.
