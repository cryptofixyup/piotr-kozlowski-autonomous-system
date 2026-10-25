-- Preserve actual inputs, not a reference to the mutable current order.
-- Historical decisions remain NULL: their original inputs cannot be reconstructed.
ALTER TABLE optimization_decisions ADD COLUMN request_snapshot JSONB;

CREATE FUNCTION protect_decision_request_snapshot() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.request_snapshot IS NULL OR jsonb_typeof(NEW.request_snapshot) <> 'object' THEN
            RAISE EXCEPTION 'New decisions require a request snapshot' USING ERRCODE = '23514';
        END IF;
    ELSIF NEW.request_snapshot IS DISTINCT FROM OLD.request_snapshot THEN
        RAISE EXCEPTION 'Decision request snapshots are immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER decision_request_snapshot_guard
BEFORE INSERT OR UPDATE ON optimization_decisions
FOR EACH ROW EXECUTE FUNCTION protect_decision_request_snapshot();

-- Match the API's finite numeric domain without truncating tiny positive inputs
-- or overflowing on a large loss percentage. Arithmetic overflow is rejected by
-- the application before persistence. Existing values are retained unchanged.
ALTER TABLE orders
    ALTER COLUMN weight_kg TYPE NUMERIC,
    ALTER COLUMN revenue_pln TYPE NUMERIC;
ALTER TABLE optimization_decisions
    ALTER COLUMN cost_pln TYPE NUMERIC,
    ALTER COLUMN margin_pln TYPE NUMERIC,
    ALTER COLUMN margin_pct TYPE NUMERIC;
