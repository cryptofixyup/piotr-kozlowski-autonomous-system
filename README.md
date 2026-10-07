# Piotr Kozłowski — Autonomous Operations System

Production-oriented scaffold for a fully automated operations ecosystem, starting with Logi-Agent logistics optimization.

## Scope
- Orders, fleet, carriers and routes
- Deterministic cost/margin optimization
- Backhaul and consolidation extension points
- AI orchestration boundary
- Policy gates, auditability and observability
- CI/CD developer handoff

## Design principle
Deterministic business rules remain the source of truth. AI enriches, ranks and explains; it does not override hard constraints.

## Run locally
```bash
docker compose up --build
curl http://localhost:8000/health
```

API docs: http://localhost:8000/docs

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
