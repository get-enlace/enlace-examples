# enlace-examples / nest

A minimal NestJS API implementing the [shared example contract](../CONTRACT.md) — in-memory
`Customers`, `Products`, and `Orders` — wired up with [`enlace-js`](../../enlace-js)'s
`@get-enlace/nest` package, installed from its `dev` dist-tag (always the latest dev build,
published automatically on every push to `enlace-js`'s `main`).

The OpenAPI document is generated at startup by [`@nestjs/swagger`](https://docs.nestjs.com/openapi/introduction)
from the `@ApiOperation`/`@ApiProperty` decorators on the controllers and `src/dto.ts`, not
hand-written.

## Setup

`@get-enlace/nest` (and its own `@get-enlace/ui` dependency) live on GitHub Packages, which
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
canvas — it works unmodified against this example, [`express`](../express), or
[`aspnetcore`](../aspnetcore), since all three implement the exact same contract.

## Notes

- `ContractErrorFilter` (`src/contract-error.filter.ts`) rewrites Nest's default exception body
  (`{ statusCode, message, error }`) into the contract's required shape (`{ "error": "<message>" }`)
  — controllers just `throw new NotFoundException(...)`/`BadRequestException(...)` and stay
  framework-idiomatic.
- `app.module.ts` imports `EnlaceModule` directly — no `forRoot()`, no config. `main.ts` calls
  `EnlaceModule.setSpec(app, SwaggerModule.createDocument(...))` — a single line — after the app
  instance exists, which is when `@nestjs/swagger` can actually build the document. The adapter
  reads the spec fresh on every request, so it's live by the time any browser hits `/enlace`.
- `package.json` depends on `@get-enlace/nest` via the `dev` dist-tag, not a pinned version — the
  next `npm install` (or `rm -rf node_modules package-lock.json && npm install`, since `npm ci`
  would otherwise reinstall whatever the lockfile already resolved) always picks up whatever's
  newest.
