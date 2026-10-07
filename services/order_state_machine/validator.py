from .models import OrderStatus
from .transitions import ALLOWED_TRANSITIONS

class InvalidOrderTransition(ValueError):
    pass

def validate_transition(current: OrderStatus, target: OrderStatus) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, ()):
        raise InvalidOrderTransition(f"Invalid order transition: {current.value} -> {target.value}")
