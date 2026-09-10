# enlace-examples / java

A minimal Spring Boot Web API (springdoc, zero Enlace config beyond the dependency itself)
implementing the [shared example contract](../CONTRACT.md) — in-memory `Customers`,
`Products`, and `Orders` — wired up with [`enlace-java`](../../enlace-java)'s
`enlace-spring-boot-starter`.

`enlace-java` has no publishing pipeline yet (see its
[`CONTRIBUTING.md`](../../enlace-java/CONTRIBUTING.md)), so unlike [`aspnetcore`](../aspnetcore)
this example can't install the adapter from a registry — it resolves it from your local Maven
repo (`~/.m2`) instead, which you populate by building `enlace-java` yourself first.

## Setup

```bash
# 1. (optional but recommended) sync a real @get-enlace/ui bundle into enlace-java, so
#    the canvas actually renders instead of just the API — without this step the app
#    still runs and /enlace/api/spec still resolves, but /enlace itself 404s.
(cd ../../enlace-java && ./scripts/dev-sync-ui.sh ../enlace-ui)

# 2. build and install enlace-java into your local Maven repo — this example's pom.xml
#    depends on io.github.get-enlace:enlace-spring-boot-starter:0.0.1-SNAPSHOT, which only
#    exists locally until that changes
(cd ../../enlace-java && mvn install)
```

## Picking up a newer local build

Whenever `enlace-java` changes, repeat step 2 above (and step 1 too, if `enlace-ui` also
changed) and restart this app — Maven resolves `0.0.1-SNAPSHOT` from whatever's currently in
your local repo, no version bump needed for a SNAPSHOT.

## Run

```bash
mvn spring-boot:run
```

Open `http://localhost:8080/enlace` for the UI, or `http://localhost:8080/enlace/api/spec`
to see the resolved OpenAPI doc directly. `/swagger-ui.html` (springdoc's own UI) and
`/customers`, `/products`, `/orders` (the sample API) are also live. See
[`CONTRACT.md`](../CONTRACT.md#reference-demo-chain) for a chain to try on the canvas — it
works unmodified against [`aspnetcore`](../aspnetcore), [`express`](../express), or
[`nest`](../nest) too, since all four implement the exact same contract.
