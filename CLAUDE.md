# Repository Invariants

## Logistics P0
- Order lifecycle transitions are deterministic and fail closed.
- Database access is isolated behind the DAL packages.
- Assignment and KPI decision engines must remain deterministic and testable.
- Operational actions must be auditable through persisted events.

## CI
- Python tests run with apps/api on PYTHONPATH.
- Security and dependency workflows must fail only on actionable findings or configuration errors.
