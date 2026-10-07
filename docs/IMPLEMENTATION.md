# Implementation Roadmap

## P0 — Correctness and safety
- [ ] Canonical domain models
- [ ] PostgreSQL persistence and migrations
- [ ] Idempotency keys for commands
- [ ] Hard feasibility/compliance validation
- [ ] Deterministic cost and margin calculation outside LLM
- [ ] Append-only audit records
- [ ] Dry-run before autonomous execution
- [ ] RBAC/authentication

## P1 — Logistics optimization
- [ ] Vehicle selection
- [ ] Carrier scoring
- [ ] Cost/margin engine
- [ ] Backhaul candidate engine
- [ ] Consolidation candidate engine
- [ ] Order profitability scoring
- [ ] Exception queue
- [ ] Notifications

## P2 — Automation
- [ ] Redis/Celery event queue
- [ ] Scheduled ingestion
- [ ] Retries with exponential backoff
- [ ] Dead-letter queue
- [ ] Policy engine
- [ ] Safe auto-approval for explicitly permitted actions
- [ ] Real-time KPI updates

## P3 — Authorized integrations
Use official APIs/contracts where available.
- [ ] Routing/maps
- [ ] Load-board APIs
- [ ] Telematics/GPS
- [ ] Email/webhooks
- [ ] ERP/accounting

## P4 — AI
AI may extract structured fields, classify free text, rank feasible options and explain decisions.
AI must not invent costs/distances, bypass hard constraints, or execute irreversible actions without a policy gate.

## Definition of done
Tests pass, failure modes are explicit, audit events exist, metrics exist, retries are safe, secrets are externalized, and docs are updated.
