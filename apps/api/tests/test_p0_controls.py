from app.audit import build_audit_event
from app.idempotency import make_idempotency_key
from app.policy import evaluate_margin

def test_negative_margin_is_rejected():
    d = evaluate_margin(-1, 20)
    assert not d.allowed
    assert d.reason == "negative_margin"

def test_below_target_requires_approval():
    d = evaluate_margin(10, 20)
    assert not d.allowed
    assert d.requires_approval

def test_idempotency_is_deterministic():
    payload = {"order_id": "O1", "amount": 100}
    assert make_idempotency_key("optimize", payload) == make_idempotency_key("optimize", payload)

def test_audit_event_contains_required_fields():
    event = build_audit_event("test.event", "O1", "system", {"ok": True})
    assert event["event_type"] == "test.event"
    assert event["aggregate_id"] == "O1"
    assert event["actor"] == "system"
    assert event["payload"]["ok"] is True
