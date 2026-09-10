<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg">
  <img alt="Enlace" src="https://raw.githubusercontent.com/get-enlace/enlace-examples/main/brand/lockup-light.svg" width="280">
</picture>

# enlace-examples

Sample apps that consume Enlace's per-framework adapters, used to test each adapter
locally before publishing (and to sanity-check the published package afterwards).

One directory per language/framework:

| Directory | Adapter under test | Adapter repo |
|---|---|---|
| [`aspnetcore/`](aspnetcore) | `Enlace.AspNetCore` | [`enlace-dotnet`](../enlace-dotnet) |
| [`express/`](express) | `@get-enlace/express` | [`enlace-js`](../enlace-js) |
| [`nest/`](nest) | `@get-enlace/nest` | [`enlace-js`](../enlace-js) |
| [`java/`](java) | `enlace-spring-boot-starter` | [`enlace-java`](../enlace-java) |
| [`fastapi/`](fastapi) | `enlace-fastapi` | [`enlace-python`](../enlace-python) |

Each example directory is self-contained: its own build tooling, its own package-manager
config pointing at a local build of its adapter, and its own README with setup/run
instructions. All of them implement the **same** API — see [`CONTRACT.md`](CONTRACT.md) —
so a chain built on the canvas against one language's example works unmodified against
any other's.
