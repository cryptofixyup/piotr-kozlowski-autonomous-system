from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class KPIState:
    avg_margin_pct: Decimal
    backhaul_ratio: Decimal
    consolidation_ratio: Decimal
    vehicle_utilization: Decimal
    carrier_utilization: Decimal
    sla_rate: Decimal
