from .audit import build_audit_event
from .policy import PolicyDecision, evaluate_margin
from .schemas import OptimizeRequest


def select_vehicle(request: OptimizeRequest):
    candidates = [
        v for v in request.vehicles
        if v.available and v.capacity_kg >= request.order.weight_kg
    ]
    return min(candidates, key=lambda v: (v.capacity_kg, v.fuel_l_per_100km), default=None)


def carrier_score(carrier) -> float:
    cost_component = 1 / (1 + carrier.cost_per_km)
    return (
        0.35 * (carrier.rating / 5)
        + 0.15 * carrier.availability
        + 0.10 * float(carrier.verified)
        + 0.40 * cost_component
    )


def select_carrier(request: OptimizeRequest):
    candidates = [c for c in request.carriers if c.availability > 0 and c.verified]
    return max(candidates, key=carrier_score, default=None)


def _rejection(request: OptimizeRequest, reason: str, actor_id: str) -> dict:
    result = {
        "decision": "reject",
        "reason": reason,
        "requires_approval": False,
    }
    result["audit_event"] = build_audit_event(
        "order.optimization.rejected",
        request.order.id,
        actor_id,
        result.copy(),
    )
    return result


def optimize_order(request: OptimizeRequest, actor_id: str = "system"):
    vehicle = select_vehicle(request)
    carrier = select_carrier(request)

    if vehicle is None:
        return _rejection(request, "no_feasible_vehicle", actor_id)
    if carrier is None:
        return _rejection(request, "no_verified_carrier", actor_id)

    fuel_cost = (
        request.route.distance_km / 100
        * vehicle.fuel_l_per_100km
        * request.fuel_price_pln_per_litre
    )
    carrier_cost = request.route.distance_km * carrier.cost_per_km
    total_cost = fuel_cost + carrier_cost + request.route.toll_cost_pln
    margin_pln = request.order.revenue_pln - total_cost

    if request.order.revenue_pln == 0:
        margin_pct = None
        policy = PolicyDecision(False, "negative_margin")
    else:
        margin_pct = 100 * margin_pln / request.order.revenue_pln
        policy = evaluate_margin(margin_pct, request.target_margin_pct)

    result = {
        "decision": "approve" if policy.allowed else ("review" if policy.requires_approval else "reject"),
        "reason": policy.reason,
        "vehicle_id": vehicle.id,
        "carrier_id": carrier.id,
        "cost_pln": round(total_cost, 2),
        "margin_pln": round(margin_pln, 2),
        "margin_pct": round(margin_pct, 2) if margin_pct is not None else None,
        "requires_approval": policy.requires_approval,
    }
    result["audit_event"] = build_audit_event(
        "order.optimization.completed",
        request.order.id,
        actor_id,
        result.copy(),
    )
    return result
