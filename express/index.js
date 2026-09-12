import express from 'express';
import swaggerJsdoc from 'swagger-jsdoc';
import { enlace } from '@get-enlace/express';

const app = express();
app.use(express.json());

const port = process.env.PORT || 4000;

// Generated from the @openapi JSDoc blocks on each route below, not
// hand-written — swagger-jsdoc scans this file at startup and builds the
// document from those annotations plus the shared component schemas
// declared in `definition` here.
const spec = swaggerJsdoc({
  definition: {
    openapi: '3.0.3',
    info: { title: 'Enlace Example API (Express)', version: '1.0.0' },
    // No `servers` entry on purpose — Enlace UI resolves the request base
    // URL against wherever the spec document itself was fetched from
    // (enlace-ui's resolveBaseUrl, per the OpenAPI Server Object's own
    // default of `/` when `servers` is omitted), so this works unmodified
    // on any deployment (localhost, Render, etc). An earlier hardcoded
    // `servers=[{"url": "http://localhost:4000"}]` here was a workaround
    // for a real gap in enlace-ui, since fixed there.
    components: {
      schemas: {
        Customer: {
          type: 'object',
          properties: { id: { type: 'integer' }, name: { type: 'string' }, email: { type: 'string' } },
        },
        CustomerRequest: {
          type: 'object',
          required: ['name', 'email'],
          properties: { name: { type: 'string' }, email: { type: 'string' } },
        },
        Product: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            name: { type: 'string' },
            price: { type: 'number' },
            stock: { type: 'integer' },
          },
        },
        ProductRequest: {
          type: 'object',
          required: ['name', 'price', 'stock'],
          properties: { name: { type: 'string' }, price: { type: 'number' }, stock: { type: 'integer' } },
        },
        OrderItem: {
          type: 'object',
          properties: {
            productId: { type: 'integer' },
            quantity: { type: 'integer' },
            unitPrice: { type: 'number' },
          },
        },
        OrderItemRequest: {
          type: 'object',
          required: ['productId', 'quantity'],
          properties: { productId: { type: 'integer' }, quantity: { type: 'integer' } },
        },
        Order: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            customerId: { type: 'integer' },
            status: { type: 'string', enum: ['pending', 'paid', 'shipped', 'cancelled'] },
            items: { type: 'array', items: { $ref: '#/components/schemas/OrderItem' } },
            total: { type: 'number' },
            createdAt: { type: 'string', format: 'date-time' },
          },
        },
        OrderRequest: {
          type: 'object',
          required: ['customerId', 'items'],
          properties: {
            customerId: { type: 'integer' },
            items: { type: 'array', items: { $ref: '#/components/schemas/OrderItemRequest' } },
          },
        },
        OrderStatusRequest: {
          type: 'object',
          required: ['status'],
          properties: { status: { type: 'string', enum: ['pending', 'paid', 'shipped', 'cancelled'] } },
        },
        Error: {
          type: 'object',
          properties: { error: { type: 'string' } },
        },
      },
    },
  },
  apis: ['./index.js'],
});

// Enlace UI + resolved-spec endpoint, mounted at /enlace.
app.use('/enlace', enlace({ spec }));

// ---------------------------------------------------------------------------
// Shared example API — see ../CONTRACT.md. In-memory only, resets on
// restart. Customers and Products are independent CRUDs; Orders references
// both, giving a workflow with real cross-node data to chain on the canvas.
// ---------------------------------------------------------------------------

const customers = new Map();
let nextCustomerId = 1;

const products = new Map();
let nextProductId = 1;

const orders = new Map();
let nextOrderId = 1;

function notFound(res, message) {
  return res.status(404).json({ error: message });
}

function badRequest(res, message) {
  return res.status(400).json({ error: message });
}

// --- Customers -------------------------------------------------------------

/**
 * @openapi
 * /customers:
 *   get:
 *     operationId: listCustomers
 *     summary: List customers
 *     responses:
 *       200:
 *         description: Customers
 *         content:
 *           application/json:
 *             schema: { type: array, items: { $ref: '#/components/schemas/Customer' } }
 */
app.get('/customers', (req, res) => {
  res.json([...customers.values()]);
});

/**
 * @openapi
 * /customers/{id}:
 *   get:
 *     operationId: getCustomer
 *     summary: Fetch a customer by id
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       200:
 *         description: Customer found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Customer' } } }
 *       404:
 *         description: Customer not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.get('/customers/:id', (req, res) => {
  const customer = customers.get(Number(req.params.id));
  if (!customer) return notFound(res, `Customer ${req.params.id} not found.`);
  res.json(customer);
});

/**
 * @openapi
 * /customers:
 *   post:
 *     operationId: createCustomer
 *     summary: Create a customer
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/CustomerRequest' } } }
 *     responses:
 *       201:
 *         description: Customer created
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Customer' } } }
 */
app.post('/customers', (req, res) => {
  const { name, email } = req.body;
  const customer = { id: nextCustomerId++, name, email };
  customers.set(customer.id, customer);
  res.status(201).json(customer);
});

/**
 * @openapi
 * /customers/{id}:
 *   put:
 *     operationId: updateCustomer
 *     summary: Update a customer
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/CustomerRequest' } } }
 *     responses:
 *       200:
 *         description: Customer updated
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Customer' } } }
 *       404:
 *         description: Customer not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.put('/customers/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!customers.has(id)) return notFound(res, `Customer ${id} not found.`);
  const { name, email } = req.body;
  const customer = { id, name, email };
  customers.set(id, customer);
  res.json(customer);
});

/**
 * @openapi
 * /customers/{id}:
 *   delete:
 *     operationId: deleteCustomer
 *     summary: Delete a customer
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       204:
 *         description: Customer deleted
 *       404:
 *         description: Customer not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.delete('/customers/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!customers.delete(id)) return notFound(res, `Customer ${id} not found.`);
  res.status(204).end();
});

// --- Products ----------------------------------------------------------------

/**
 * @openapi
 * /products:
 *   get:
 *     operationId: listProducts
 *     summary: List products
 *     responses:
 *       200:
 *         description: Products
 *         content:
 *           application/json:
 *             schema: { type: array, items: { $ref: '#/components/schemas/Product' } }
 */
app.get('/products', (req, res) => {
  res.json([...products.values()]);
});

/**
 * @openapi
 * /products/{id}:
 *   get:
 *     operationId: getProduct
 *     summary: Fetch a product by id
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       200:
 *         description: Product found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Product' } } }
 *       404:
 *         description: Product not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.get('/products/:id', (req, res) => {
  const product = products.get(Number(req.params.id));
  if (!product) return notFound(res, `Product ${req.params.id} not found.`);
  res.json(product);
});

/**
 * @openapi
 * /products:
 *   post:
 *     operationId: createProduct
 *     summary: Create a product
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/ProductRequest' } } }
 *     responses:
 *       201:
 *         description: Product created
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Product' } } }
 */
app.post('/products', (req, res) => {
  const { name, price, stock } = req.body;
  const product = { id: nextProductId++, name, price, stock };
  products.set(product.id, product);
  res.status(201).json(product);
});

/**
 * @openapi
 * /products/{id}:
 *   put:
 *     operationId: updateProduct
 *     summary: Update a product
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/ProductRequest' } } }
 *     responses:
 *       200:
 *         description: Product updated
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Product' } } }
 *       404:
 *         description: Product not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.put('/products/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!products.has(id)) return notFound(res, `Product ${id} not found.`);
  const { name, price, stock } = req.body;
  const product = { id, name, price, stock };
  products.set(id, product);
  res.json(product);
});

/**
 * @openapi
 * /products/{id}:
 *   delete:
 *     operationId: deleteProduct
 *     summary: Delete a product
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       204:
 *         description: Product deleted
 *       404:
 *         description: Product not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.delete('/products/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!products.delete(id)) return notFound(res, `Product ${id} not found.`);
  res.status(204).end();
});

// --- Orders --------------------------------------------------------------------

/**
 * @openapi
 * /orders:
 *   get:
 *     operationId: listOrders
 *     summary: List orders
 *     responses:
 *       200:
 *         description: Orders
 *         content:
 *           application/json:
 *             schema: { type: array, items: { $ref: '#/components/schemas/Order' } }
 */
app.get('/orders', (req, res) => {
  res.json([...orders.values()]);
});

/**
 * @openapi
 * /orders/{id}:
 *   get:
 *     operationId: getOrder
 *     summary: Fetch an order by id
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       200:
 *         description: Order found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Order' } } }
 *       404:
 *         description: Order not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.get('/orders/:id', (req, res) => {
  const order = orders.get(Number(req.params.id));
  if (!order) return notFound(res, `Order ${req.params.id} not found.`);
  res.json(order);
});

/**
 * @openapi
 * /orders:
 *   post:
 *     operationId: createOrder
 *     summary: Create an order (references an existing customer + products)
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/OrderRequest' } } }
 *     responses:
 *       201:
 *         description: Order created
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Order' } } }
 *       400:
 *         description: Unknown customerId or productId
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.post('/orders', (req, res) => {
  const { customerId, items } = req.body;
  if (!customers.has(customerId)) {
    return badRequest(res, `customerId ${customerId} does not exist.`);
  }

  const resolvedItems = [];
  for (const item of items) {
    const product = products.get(item.productId);
    if (!product) {
      return badRequest(res, `productId ${item.productId} does not exist.`);
    }
    resolvedItems.push({ productId: item.productId, quantity: item.quantity, unitPrice: product.price });
  }

  const total = resolvedItems.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);
  const order = {
    id: nextOrderId++,
    customerId,
    status: 'pending',
    items: resolvedItems,
    total,
    createdAt: new Date().toISOString(),
  };
  orders.set(order.id, order);
  res.status(201).json(order);
});

/**
 * @openapi
 * /orders/{id}/status:
 *   put:
 *     operationId: updateOrderStatus
 *     summary: Update an order's status
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     requestBody:
 *       required: true
 *       content: { application/json: { schema: { $ref: '#/components/schemas/OrderStatusRequest' } } }
 *     responses:
 *       200:
 *         description: Order updated
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Order' } } }
 *       404:
 *         description: Order not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.put('/orders/:id/status', (req, res) => {
  const id = Number(req.params.id);
  const order = orders.get(id);
  if (!order) return notFound(res, `Order ${id} not found.`);
  const updated = { ...order, status: req.body.status };
  orders.set(id, updated);
  res.json(updated);
});

/**
 * @openapi
 * /orders/{id}:
 *   delete:
 *     operationId: deleteOrder
 *     summary: Delete an order
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema: { type: integer }
 *     responses:
 *       204:
 *         description: Order deleted
 *       404:
 *         description: Order not found
 *         content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } }
 */
app.delete('/orders/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!orders.delete(id)) return notFound(res, `Order ${id} not found.`);
  res.status(204).end();
});

app.listen(port, () => {
  console.log(`Enlace example (Express) running at http://localhost:${port}`);
  console.log(`  Canvas:  http://localhost:${port}/enlace`);
  console.log(`  Spec:    http://localhost:${port}/enlace/api/spec`);
});
