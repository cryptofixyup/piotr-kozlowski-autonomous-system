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

## Merge blocker repair — 2026-10-25

Test-only commit `8855943130acf23e13a406cf7eab5180b2c9cc51` reproduced four failures against PostgreSQL in Actions run `40241402164`: disabled execution guard, default connection timeout, concurrent migration bootstrap and per-version migration recovery (4 failed, 26 passed).

The repair serializes schema bootstrap and all migration checks with a session advisory lock, uses explicit transactions per version, and adds a five-second connection timeout unless DATABASE_URL specifies one. The P0 execution guard returns true. Compose no longer publishes passwordless PostgreSQL; the API image runs as UID/GID 10001.

Workflow actions are pinned to verified commit SHAs. Gitleaks uses a checksum-verified CLI and the complete PR base/head range (no API pagination); `.gitleaksignore` suppresses only the verified historical documentation idempotency-key example. TruffleHog's duplicate flag is removed. GitGuardian uses its actual upstream commit and default CI command. Optional GitGuardian/Snyk credentials remain optional and their absence is recorded, not claimed as scanner success. Bandit excludes only test paths and tool directories while retaining application scanning. Pytest now permits the audit-reported fixed major version; Dependabot covers both requirements files and GitHub Actions.

Local validation: pytest 9.1.1 reports 23 passed, 7 database-dependent tests skipped; Bandit reports zero findings; Gitleaks scans all 48 original PR commits without findings using the exact documented suppression. PostgreSQL integration and hosted scanner results must be verified on the repair head before merge.

### Hosted follow-up

Repair head `79e85ec4f1f5ac87a71fab5c681a5f20b7fc3aa7` passed all 30 application/PostgreSQL tests in run `40241596625`. Hosted scanning exposed three missing Dependabot cooldown blocks and two unverified PostgreSQL detections in historical commit `f0970a1d9a1d78bb90877e11385877246c9c78ee`, `docker-compose.yml` lines 19/33. The historical source was checked: both used the removed local development Compose credential.

Dependabot now waits seven days for version updates. TruffleHog uses its checksum-verified 3.99.7 CLI with all detectors enabled, complete history/range coverage and scan-error failure enabled. The report gate accepts only the two exact historical locations, detector, unverified state and raw SHA-256; new occurrences, changed values and verified findings remain blocking. Malformed reports and scanner failures fail closed. Twelve regression cases cover these boundaries; credential values are not printed by the gate.
