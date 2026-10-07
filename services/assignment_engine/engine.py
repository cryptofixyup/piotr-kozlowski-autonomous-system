from dataclasses import dataclass
from .scoring import vehicle_score, carrier_score

@dataclass(frozen=True, slots=True)
class AssignmentDecision:
    vehicle_id: str
    carrier_id: str
    confidence: float

def assign(order, vehicles, carriers) -> AssignmentDecision | None:
    vehicles = [(vehicle_score(v, order), v) for v in vehicles]
    carriers = [(carrier_score(c), c) for c in carriers]
    vehicles = [x for x in vehicles if x[0] >= 0]
    carriers = [x for x in carriers if x[0] >= 0]
    if not vehicles or not carriers:
        return None
    vehicle_score_value, vehicle = max(vehicles, key=lambda x: x[0])
    carrier_score_value, carrier = max(carriers, key=lambda x: x[0])
    confidence = max(0.0, min(1.0, (vehicle_score_value + carrier_score_value) / 2.0))
    return AssignmentDecision(vehicle.id, carrier.id, round(confidence, 4))
