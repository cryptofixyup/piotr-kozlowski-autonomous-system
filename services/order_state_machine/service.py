from dataclasses import dataclass
from .models import OrderStatus
from .validator import validate_transition

@dataclass(frozen=True, slots=True)
class OrderState:
    status: OrderStatus

def transition(state: OrderState, target: OrderStatus) -> OrderState:
    validate_transition(state.status, target)
    return OrderState(status=target)
