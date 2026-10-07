CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT NOT NULL,
    pickup_city TEXT NOT NULL,
    delivery_city TEXT NOT NULL,
    cargo_type TEXT,
    weight_kg NUMERIC(12,2) NOT NULL CHECK (weight_kg > 0),
    revenue_pln NUMERIC(14,2) NOT NULL CHECK (revenue_pln >= 0),
    status TEXT NOT NULL CHECK (status IN ('NEW','VALIDATED','ASSIGNED','ROUTE_OPTIMIZED','IN_TRANSIT','DELIVERED','INVOICED','CLOSED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration TEXT NOT NULL UNIQUE,
    vehicle_type TEXT NOT NULL,
    capacity_kg NUMERIC(12,2) NOT NULL CHECK (capacity_kg > 0),
    fuel_l_per_100km NUMERIC(8,3) NOT NULL CHECK (fuel_l_per_100km > 0),
    available BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS carriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    vat_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ocp_valid BOOLEAN NOT NULL DEFAULT FALSE,
    rating NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating >= 0 AND rating <= 5),
    cost_per_km NUMERIC(10,4) NOT NULL DEFAULT 0,
    availability NUMERIC(5,4) NOT NULL DEFAULT 1 CHECK (availability >= 0 AND availability <= 1)
);

CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    distance_km NUMERIC(12,2) NOT NULL,
    toll_cost_pln NUMERIC(12,2) NOT NULL DEFAULT 0,
    optimized BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    carrier_id UUID NOT NULL REFERENCES carriers(id),
    confidence NUMERIC(6,5) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    value NUMERIC(18,6) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity TEXT NOT NULL CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_assignments_order ON assignments(order_id);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON event_log(aggregate_type, aggregate_id, created_at);
