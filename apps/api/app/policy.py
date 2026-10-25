from dataclasses import dataclass

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False

def evaluate_margin(margin_pct: float, target_margin_pct: float) -> PolicyDecision:
    if margin_pct < 0:
        return PolicyDecision(False, "negative_margin")
    if margin_pct < target_margin_pct:
        return PolicyDecision(False, "below_target_margin", requires_approval=True)
    return PolicyDecision(True, "target_margin_met")
