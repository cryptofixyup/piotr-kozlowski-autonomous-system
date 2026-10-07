# P0 Hardening

Implemented on this branch:

- deterministic policy gate;
- negative-margin rejection;
- below-target margin requires approval;
- deterministic idempotency-key generation;
- authenticated actor identity at the API boundary;
- atomic PostgreSQL persistence;
- transactional outbox;
- structured audit-event contract;
- migration runner and deployment wiring;
- PostgreSQL integration test coverage.

## Execution rule

The LLM must never be the final authority for feasibility, arithmetic, compliance, authorization, or irreversible execution.

Execution sequence:

1. validate input;
2. authenticate actor;
3. deterministic optimization;
4. calculate economics;
5. policy gate;
6. create audit event;
7. persist decision, audit event, and outbox event atomically;
8. return the idempotent result;
9. execute only through a future outbox consumer;
10. emit outcome event.

## Persistence boundary

Every mutation requires an `Idempotency-Key`. The same key may only be reused for the same request payload and authenticated actor. A conflicting reuse returns `409 Conflict`.

The optimization decision, audit event, idempotency record, and outbox event are committed in one PostgreSQL transaction. If any write fails, none of them is committed.

The outbox is intentionally inert in P0.2: no external execution consumer is enabled.

## Authentication boundary

`Authorization: Bearer <token>` is required for mutation endpoints. The configured token maps to `AUTONOMOUS_ACTOR_ID`, so the caller cannot self-assert an actor identity with a separate header.

This is an authenticated API boundary, not a final enterprise IAM implementation. OIDC/JWT/service identity can replace the token verifier without changing the persistence contract.

## Local execution

```bash
docker compose up --build
curl http://localhost:8000/health
```

For `/v1/optimize`, send:

```text
Authorization: Bearer local-dev-token
Idempotency-Key: optimize-order-001
```

## Safety boundary

Autonomous external execution remains disabled. The outbox records durable intent/evidence but no worker consumes it yet.
