# P0 Hardening

Implemented on this branch:

- deterministic policy gate;
- negative-margin rejection;
- below-target margin requires approval;
- deterministic idempotency-key generation;
- structured audit-event contract;
- PostgreSQL persistence foundation;
- tests for safety primitives.

## Execution rule

The LLM must never be the final authority for feasibility, arithmetic, compliance, authorization, or irreversible execution.

Execution sequence:

1. validate input;
2. deterministic optimization;
3. calculate economics;
4. policy gate;
5. create audit event;
6. persist decision idempotently;
7. execute only if policy permits;
8. emit outcome event.

## Next P0

- wire migration into deployment;
- persist optimization decisions;
- enforce Idempotency-Key at API boundary;
- add authenticated actor identity;
- add transactional outbox;
- add PostgreSQL integration tests.
