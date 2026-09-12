# enlace-examples / aspnetcore

A minimal ASP.NET Core Web API (Swashbuckle, zero Enlace config beyond `AddEnlace()`)
implementing the [shared example contract](../CONTRACT.md) — in-memory `Customers`,
`Products`, and `Orders` — wired up with [`enlace-dotnet`](../../enlace-dotnet)'s
`Enlace.AspNetCore` package, installed from GitHub Packages' dev feed (always has the latest
dev build, published automatically on every push to `enlace-dotnet`'s `main`).

## Setup

GitHub Packages requires auth even for public reads. Set `GITHUB_USERNAME`/`GITHUB_TOKEN` (a
PAT with `read:packages`) in the environment before restoring:

```bash
export GITHUB_USERNAME=<your GitHub username>
export GITHUB_TOKEN=<a PAT with read:packages>
dotnet restore
```

## Picking up a newer dev build

`Enlace.Examples.Dotnet.csproj`'s `Enlace.AspNetCore` reference is pinned to a specific dev
version rather than floating — NuGet has no dist-tag equivalent, so there's no "always latest"
reference to depend on the way the JS examples can. Bump it by hand:

```bash
dotnet add package Enlace.AspNetCore --version <new-version>
```

Find the current latest at
[github.com/get-enlace/enlace-dotnet/pkgs/nuget/Enlace.AspNetCore](https://github.com/get-enlace/enlace-dotnet/pkgs/nuget/Enlace.AspNetCore).

## Testing against a local (unpublished) build instead

Uncomment the `enlace-local` source in `nuget.config` (and comment out `enlace-github` if you
want to skip GitHub Packages auth entirely for local iteration). Whenever `enlace-dotnet`
changes:

```bash
# 1. build the real @get-enlace/ui bundle and sync it into enlace-dotnet's wwwroot-embedded
(cd ../../enlace-ui && npm run build)
../../enlace-dotnet/scripts/dev-sync-ui.sh ../../enlace-ui

# 2. bump <Version> in ../../enlace-dotnet/src/Enlace.AspNetCore/Enlace.AspNetCore.csproj
#    (NuGet caches by version — packing the same version again won't refresh a restore
#    that already pulled it), then repack
(cd ../../enlace-dotnet && dotnet pack src/Enlace.AspNetCore -c Release -o artifacts/nuget)

# 3. point this project at the new version and restore
dotnet add package Enlace.AspNetCore --version <new-version>
```

## Run

```bash
dotnet run
```

Open `http://localhost:<port>/enlace` for the UI, or
`http://localhost:<port>/enlace/api/spec` to see the resolved OpenAPI doc directly.
`/swagger` (Swagger UI) and `/customers`, `/products`, `/orders` (the sample API) are also
live in Development. See [`CONTRACT.md`](../CONTRACT.md#reference-demo-chain) for a chain
to try on the canvas — it works unmodified against [`express`](../express) or
[`nest`](../nest) too, since all three implement the exact same contract.

## Authentication & Full Contract

This example implements the basic CRUD contract (Customers, Products, Orders). For the **complete reference implementation** with full authentication (Customer JWT, Admin JWT, Carrier API Key) and the multi-step cascade workflow, see the [FastAPI example](../fastapi) (`../fastapi/README.md`) — it includes the OAuth2 token endpoint and credential setup required for the full 8-step chain demonstrated in [TESTING.md](../TESTING.md).
