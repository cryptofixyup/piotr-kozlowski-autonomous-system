from app.audit import build_audit_event
from app.idempotency import make_idempotency_key
from app.policy import evaluate_margin


def test_negative_margin_is_rejected():
    d = evaluate_margin(-1, 20)
    assert not d.allowed
    assert d.reason == "negative_margin"
    assert not d.requires_approval


def test_below_target_requires_approval():
    d = evaluate_margin(10, 20)
    assert not d.allowed
    assert d.requires_approval


def test_target_margin_is_allowed():
    d = evaluate_margin(20, 20)
    assert d.allowed
    assert d.reason == "target_margin_met"


def test_zero_margin_requires_review_when_target_is_positive():
    d = evaluate_margin(0, 20)
    assert not d.allowed
    assert d.requires_approval


def test_idempotency_is_deterministic_and_domain_separated():
    payload = {"order_id": "O1", "amount": 100}
    reordered = {"amount": 100, "order_id": "O1"}
    assert make_idempotency_key("optimize", payload) == make_idempotency_key("optimize", reordered)
    assert make_idempotency_key("optimize", payload) != make_idempotency_key("optimize", {"order_id": "O2", "amount": 100})
    assert make_idempotency_key("optimize", payload) != make_idempotency_key("execute", payload)


def test_audit_event_contains_required_fields():
    event = build_audit_event("test.event", "O1", "system", {"ok": True})
    assert event["event_type"] == "test.event"
    assert event["aggregate_id"] == "O1"
    assert event["actor"] == "system"
    assert event["payload"]["ok"] is True
