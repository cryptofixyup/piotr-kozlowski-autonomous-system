# Technical Architecture

```
External sources
    |
    v
Ingestion -> Normalization -> PostgreSQL
                           |
                           v
                 Deterministic Optimizer
                           |
                           v
                    AI Enrichment
                           |
                           v
                      Policy Gate
                           |
                           v
                       Execution
                           |
              +------------+------------+
              |                         |
              v                         v
           Audit                    KPI/Feedback
```

## Services
- API: FastAPI
- Frontend: Next.js (planned)
- Database: PostgreSQL
- Queue/cache: Redis (planned)
- Workers: Celery or equivalent (planned)
- AI: provider abstraction with typed JSON schema
- Observability: OpenTelemetry + Prometheus/Grafana (planned)
- CI: GitHub Actions

## Reliability
- idempotent commands
- transaction boundaries
- outbox events
- bounded retries
- dead-letter queue
- graceful AI/provider degradation

## Security
- least-privilege credentials
- secret injection
- validation
- RBAC
- privileged mutation audit
- no production secrets in Git
