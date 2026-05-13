# Repo Scan Checklist

A more exhaustive version of Phase 1 in `SKILL.md`. Read this when you're unsure what to look at, or when a repo doesn't fit common patterns.

## Read these first (signal-dense)

| File / pattern                                  | What it tells you                                       |
|-------------------------------------------------|---------------------------------------------------------|
| `package.json` `"main"`, `"bin"`, `"scripts"`   | Entry points, CLI commands, dev/build/test workflows    |
| `pyproject.toml` `[project.scripts]`, `entry-points` | Python entry points and console scripts            |
| `Cargo.toml` `[[bin]]`, `[lib]`                 | Rust binaries and library boundary                      |
| `go.mod` + `cmd/*/main.go`                      | Go module name and binaries                             |
| `pom.xml` `<mainClass>`                         | Java main class                                         |
| `Dockerfile` `CMD` / `ENTRYPOINT`               | What the container actually runs                        |
| `docker-compose.yml` services                   | Process boundaries in dev/prod                          |
| `k8s/*.yaml`, `helm/values.yaml`                | Deployments, services, pods, replicas, env, secrets     |
| `systemd/*.service`, `supervisord.conf`         | Process supervision and start/restart policy            |
| `Procfile`                                      | Heroku/Foreman-style process types                      |
| `.github/workflows/*.yml`                       | CI/CD pipeline → tells you the artifacts and their flow |
| `*.proto`, `openapi.yaml`, `schema.graphql`     | Wire protocols and external contracts                   |
| Migration directories (`migrations/`, `alembic/`, `flyway/`) | DB schema evolution and table inventory      |

## Find runtime units

Glob for entry-point patterns. Names vary across stacks:

- `main.{go,rs,c,cpp,py,js,ts}`
- `index.{js,ts,mjs}` at package roots
- `app.{py,rb,js,ts}`, `server.{js,ts,go,py}`, `wsgi.py`, `asgi.py`
- `cmd/*/main.go` (Go convention)
- `bin/*` (executable scripts)
- Files with `if __name__ == "__main__":` (Python)
- Files registered as `@SpringBootApplication`, `@Component`, `@Service` (Java/Kotlin)

## Find boundaries

Grep for symbols that almost always mark an architectural edge:

| Pattern                                                   | What it indicates                            |
|-----------------------------------------------------------|----------------------------------------------|
| `@RestController`, `@Controller`, `@RequestMapping`       | HTTP endpoint (Java)                         |
| `app\.(get\|post\|put\|delete)\(`                          | HTTP route (Express, Flask, etc.)            |
| `@app\.route`, `@router\.\w+`                              | Decorated HTTP route (Python)                |
| `func.*Handler`, `\w+Handler\s+struct`                    | Go HTTP handler                              |
| `grpc.NewServer`, `RegisterService`, `.proto`             | gRPC service                                 |
| `consume`, `subscribe`, `@KafkaListener`, `@SqsListener`  | Message consumer                             |
| `publish`, `produce`, `\.send\(`, `\.emit\(`              | Message producer                             |
| `CREATE TABLE`, `class \w+\(.*Model\)`, `@Entity`         | Persistence boundary                         |
| `redis.\w+Client`, `mongoose.connect`, `pg.Pool`          | External datastore client                    |
| `os.Setenv`, `process.env\.`, `getenv`                    | Runtime config — note these knobs            |

## Find state & flow

- Trace one request from entry to response. Pick a representative endpoint and follow it. That's your sequence diagram material.
- Look at startup paths: what gets initialized, in what order, what fails fast. That's often a great sequence diagram too.
- Find caches: in-process, Redis, memcached. Note TTLs and invalidation paths.
- Find queues/topics: their names are usually contracts shared with other services — note them.

## When the repo is huge

If a `find` returns thousands of files, narrow with two strategies:

1. **By language**: only look at the dominant language(s). A Python service with a `node_modules/` is still a Python service.
2. **By "leaf" entry points**: in monorepos, each app under `apps/` or `services/` is its own unit. Pick the one the user asked about.

If the user didn't specify, generate a `services-overview.html` first showing the inter-service topology, then offer to drill into one.

## Anti-patterns to watch for

- **Directory names lying.** A folder called `utils/` might contain the core business logic; a folder called `core/` might be empty boilerplate. Always confirm with code.
- **Dead code looking alive.** Files with no callers from any entry point are dead. Grep before drawing.
- **Tests pretending to be docs.** Test files often describe behavior more accurately than READMEs. If the README and the tests disagree, the tests win.
- **Generated code looking authored.** `.pb.go`, `*_pb2.py`, anything under `gen/` — note it as an artifact, not a unit.

## What to do if you can't find something

- **No entry point found**: it's probably a library. Look at the public API surface (`__init__.py`, `lib.rs`, `index.ts`) and frame the diagrams around how a *caller* would use it.
- **No deployment configs**: ask the user how it's deployed, or assume a single-process default and mark it `inferred`.
- **No README and no docs**: this is the most common case. The code is the doc. Lean harder on the entry points + the routing/wiring files.
