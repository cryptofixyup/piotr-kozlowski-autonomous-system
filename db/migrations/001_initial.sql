-- P0 persistence foundation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    external_ref TEXT UNIQUE,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    weight_kg NUMERIC(12,2) NOT NULL CHECK (weight_kg > 0),
    revenue_pln NUMERIC(14,2) NOT NULL CHECK (revenue_pln >= 0),
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS optimization_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    vehicle_id TEXT,
    carrier_id TEXT,
    cost_pln NUMERIC(14,2),
    margin_pln NUMERIC(14,2),
    margin_pct NUMERIC(8,3),
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_aggregate ON audit_events (aggregate_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_order ON optimization_decisions (order_id, created_at DESC);
