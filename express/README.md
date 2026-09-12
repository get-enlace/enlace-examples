# enlace-examples / express

A minimal Express API implementing the [shared example contract](../CONTRACT.md) — in-memory
`Customers`, `Products`, and `Orders` — wired up with [`enlace-js`](../../enlace-js)'s
`@get-enlace/express` package, installed from its `dev` dist-tag (always the latest dev build,
published automatically on every push to `enlace-js`'s `main`).

The OpenAPI document is generated at startup by [`swagger-jsdoc`](https://www.npmjs.com/package/swagger-jsdoc)
from the `@openapi` JSDoc blocks above each route in `index.js`, not hand-written.

## Setup

`@get-enlace/express` (and its own `@get-enlace/ui` dependency) live on GitHub Packages, which
requires auth even for public reads. Set a `GITHUB_TOKEN` env var to a PAT with `read:packages`
before installing:

```bash
export GITHUB_TOKEN=<a PAT with read:packages>
npm install
```

## Run

```bash
npm start
```

Open `http://localhost:4000/enlace` for the canvas, or `http://localhost:4000/enlace/api/spec` to
see the OpenAPI document directly. `/customers`, `/products`, `/orders` (the sample API) are also
live. See [`CONTRACT.md`](../CONTRACT.md#reference-demo-chain) for a chain to try on the
canvas — it works unmodified against this example, [`nest`](../nest), or
[`aspnetcore`](../aspnetcore), since all three implement the exact same contract.

## Picking up a newer dev build

`package.json` depends on `@get-enlace/express` via the `dev` dist-tag, not a pinned version — the
next `npm install` (or `rm -rf node_modules package-lock.json && npm install`, since `npm ci`
would otherwise reinstall whatever the lockfile already resolved) always picks up whatever's
newest.

## Authentication & Full Contract

This example implements the basic CRUD contract (Customers, Products, Orders). For the **complete reference implementation** with full authentication (Customer JWT, Admin JWT, Carrier API Key) and the multi-step cascade workflow, see the [FastAPI example](../fastapi) (`../fastapi/README.md`) — it includes the OAuth2 token endpoint and credential setup required for the full 8-step chain demonstrated in [TESTING.md](../TESTING.md).
