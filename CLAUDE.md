# Autonomous Operations System — Engineering Invariants

## Authority boundary

Deterministic code is authoritative for feasibility, arithmetic, policy, authorization, persistence, and irreversible execution.

LLM output may enrich, rank, explain, or propose. It must never directly authorize an operational or financial action.

## Execution pipeline

```
INPUT
  -> VALIDATION
  -> AUTHENTICATED ACTOR
  -> DETERMINISTIC OPTIMIZATION
  -> COST / MARGIN
  -> POLICY GATE
  -> AUDIT
  -> IDEMPOTENT PERSISTENCE
  -> TRANSACTIONAL OUTBOX
  -> CONTROLLED EXECUTION
  -> OUTCOME
  -> FEEDBACK
```

## Non-negotiable safety rules

1. Negative-margin decisions cannot be autonomously approved.
2. Below-target margin requires explicit approval.
3. Every mutation requires an Idempotency-Key.
4. Reusing an Idempotency-Key with a different request or actor is rejected.
5. Decision, audit, idempotency, and outbox writes must commit atomically.
6. External execution is disabled until authorization, outcome, retry, and reconciliation controls are tested.
7. Audit payloads are snapshots, not mutable references.
8. Authenticated actor identity comes from the authentication boundary, not a caller-supplied actor header.
9. PostgreSQL is the system of record for durable operational decisions.
10. Redis streams must use consumer groups for distributed consumption.

## P0.2 boundary

The transactional outbox records durable intent/evidence. No outbox consumer is enabled in P0.2.

## Development rule

Prefer the smallest maintainable implementation that preserves deterministic safety, auditability, idempotency, and transactional integrity.
