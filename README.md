<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg">
  <img alt="Enlace" src="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg" width="280">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg">
  <img alt="Enlace" src="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg" width="280">
</picture>

# enlace-examples

Sample apps that consume Enlace's per-framework adapters, used to test each adapter
locally before publishing (and to sanity-check the published package afterwards).

**🚀 Live Demo:** https://enlace-fastapi.onrender.com/enlace/

One directory per language/framework:

| Directory | Adapter under test | Adapter repo | Status |
|---|---|---|---|
| [`aspnetcore/`](aspnetcore) | `Enlace.AspNetCore` | [`enlace-dotnet`](../enlace-dotnet) | Local dev |
| [`express/`](express) | `@get-enlace/express` | [`enlace-js`](../enlace-js) | Local dev |
| [`nest/`](nest) | `@get-enlace/nest` | [`enlace-js`](../enlace-js) | Local dev |
| [`java/`](java) | `enlace-spring-boot-starter` | [`enlace-java`](../enlace-java) | Local dev |
| [`fastapi/`](fastapi) | `enlace-fastapi` | [`enlace-python`](../enlace-python) | 🚀 **Live on Render** |

Each example directory is self-contained: its own build tooling, its own package-manager
config, and its own README with setup/run instructions. All of them implement the **same** API — see [`CONTRACT.md`](CONTRACT.md) —
so a chain built on the canvas against one language's example works unmodified against
any other's.

## Quick Start

### Try the Live Demo (FastAPI on Render)

No setup needed — just open the canvas:

👉 **https://enlace-fastapi.onrender.com/enlace/**

See [`fastapi/README.md`](fastapi#testing-the-live-demo) for a complete walkthrough of the 8-step reference chain.

### Run Locally

Pick any example directory and follow its README for local setup/run instructions.
