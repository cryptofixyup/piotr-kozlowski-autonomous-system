from app.audit import build_audit_event
from app.idempotency import make_idempotency_key
from app.optimizer import optimize_order
from app.policy import evaluate_margin
from app.schemas import Carrier, OptimizeRequest, Order, Route, Vehicle


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


def test_zero_revenue_loss_is_rejected_and_audited():
    request = OptimizeRequest(
        order=Order(
            id="O-zero",
            origin="WRO",
            destination="WAW",
            weight_kg=100,
            revenue_pln=0,
        ),
        route=Route(distance_km=100, toll_cost_pln=0),
        vehicles=[
            Vehicle(id="V1", capacity_kg=1000, fuel_l_per_100km=10),
        ],
        carriers=[
            Carrier(id="C1", rating=5, cost_per_km=1, availability=1, verified=True),
        ],
        fuel_price_pln_per_litre=6,
        target_margin_pct=0,
    )

    result = optimize_order(request, actor_id="test-actor")

    assert result["decision"] == "reject"
    assert result["reason"] == "negative_margin"
    assert result["audit_event"]["event_type"] == "order.optimization.completed"
    assert result["audit_event"]["actor"] == "test-actor"
    assert result["audit_event"]["payload"]["decision"] == "reject"


def test_infeasible_decisions_are_audited():
    request = OptimizeRequest(
        order=Order(
            id="O-no-vehicle",
            origin="WRO",
            destination="WAW",
            weight_kg=1000,
            revenue_pln=5000,
        ),
        route=Route(distance_km=100, toll_cost_pln=0),
        vehicles=[
            Vehicle(id="V1", capacity_kg=100, fuel_l_per_100km=10),
        ],
        carriers=[
            Carrier(id="C1", rating=5, cost_per_km=1, availability=1, verified=True),
        ],
        fuel_price_pln_per_litre=6,
        target_margin_pct=20,
    )

    result = optimize_order(request, actor_id="test-actor")

    assert result["decision"] == "reject"
    assert result["reason"] == "no_feasible_vehicle"
    assert result["audit_event"]["event_type"] == "order.optimization.rejected"
    assert result["audit_event"]["actor"] == "test-actor"


def test_audit_payload_is_a_snapshot():
    request = OptimizeRequest(
        order=Order(
            id="O-snapshot",
            origin="WRO",
            destination="WAW",
            weight_kg=100,
            revenue_pln=5000,
        ),
        route=Route(distance_km=100, toll_cost_pln=0),
        vehicles=[
            Vehicle(id="V1", capacity_kg=1000, fuel_l_per_100km=10),
        ],
        carriers=[
            Carrier(id="C1", rating=5, cost_per_km=1, availability=1, verified=True),
        ],
        fuel_price_pln_per_litre=6,
        target_margin_pct=20,
    )

    result = optimize_order(request)
    result["decision"] = "tampered"

    assert result["audit_event"]["payload"]["decision"] != "tampered"
