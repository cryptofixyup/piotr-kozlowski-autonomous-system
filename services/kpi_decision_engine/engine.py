from dataclasses import dataclass
from .models import KPIState
from .rules import evaluate_rules

@dataclass(frozen=True, slots=True)
class DecisionResult:
    actions: tuple[str, ...]
    system_health: str

def evaluate(kpi: KPIState) -> DecisionResult:
    actions = evaluate_rules(kpi)
    if len(actions) == 0:
        health = "OPTIMAL"
    elif len(actions) <= 2:
        health = "DEGRADED"
    else:
        health = "CRITICAL"
    return DecisionResult(actions=actions, system_health=health)
