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

## Durable job runner (P0.3)

The API can persist an authenticated job request:

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer $AUTONOMOUS_API_TOKEN" \
  -H "Idempotency-Key: health-check-0001" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"health_check","payload":{},"max_attempts":3}'
```

Run one worker cycle:

```bash
cd apps/api
python -m app.worker --worker-id local-worker-1
```

Jobs are stored in PostgreSQL, claimed with row-level locking, protected by expiring worker leases, and retried a bounded number of times before dead-lettering. Repeated idempotency keys return the existing job only when the task type, payload, and retry limit match.

**Execution boundary:** only task types explicitly registered in `app.worker.HANDLERS` can run. The initial `health_check` handler is deterministic and side-effect-free. No arbitrary shell, code, repository mutation, external API action, or financial operation is executed. Add new handlers only with dedicated tests, explicit policy, and least-privilege credentials.
