# PR 3 remediation

## Changes

- Each new optimization decision stores the complete validated request as JSONB in the same transaction as the decision, audit, idempotency response and outbox. A database trigger rejects changes to that snapshot.
- Migration 003 leaves historical request snapshots NULL. It does not reconstruct unknown historical inputs from the current orders table. Pause old application writers while applying this migration and switching to the new application version: old writers do not supply the now-required snapshot.
- Numeric storage no longer has a narrower precision/scale than accepted finite API inputs. Tiny positive revenue and weight, large revenue and large loss percentages can persist. Input NaN/infinity is rejected by validation; arithmetic overflow returns 422 before any persistence. This retains the existing float arithmetic and two-decimal output rounding; it is not a conversion to exact-decimal financial arithmetic.
- Malformed non-ASCII bearer credentials return 401 rather than an unhandled TypeError.
- Missing or empty migration directories raise an error before database work, rather than reporting migrations applied.

## Regression evidence

Test-only commit d762f30d0dbc463e8ade7d22aad9e6c503c9c18c ran against PostgreSQL 16 in GitHub Actions run 40152145584: 9 failed, 16 passed. Failures reproduced missing request snapshots, monetary overflow, weight truncation, non-ASCII authentication, empty migration discovery, infinity acceptance and arithmetic overflow handling.

Run the application suite with `cd apps/api && pytest -q`. Database integration tests require DATABASE_URL and all migrations. A local run without PostgreSQL skips those tests and is not evidence of database correctness. Use the CI run for the exact repair commit as the integration result.

No execution consumer is enabled. This repair does not merge or deploy the PR.
