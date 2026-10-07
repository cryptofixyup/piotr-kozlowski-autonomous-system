from .models import KPIState

def evaluate_rules(kpi: KPIState) -> tuple[str, ...]:
    actions: list[str] = []
    if kpi.avg_margin_pct < 15:
        actions.append("REPRICE_LOW_MARGIN")
    if kpi.backhaul_ratio < 0.25:
        actions.append("SEARCH_BACKHAUL")
    if kpi.consolidation_ratio < 0.40:
        actions.append("SEARCH_CONSOLIDATION")
    if kpi.vehicle_utilization < 0.70:
        actions.append("REBALANCE_FLEET")
    if kpi.carrier_utilization < 0.60:
        actions.append("REBALANCE_CARRIERS")
    if kpi.sla_rate < 0.90:
        actions.append("PRIORITIZE_SLA")
    return tuple(actions)
