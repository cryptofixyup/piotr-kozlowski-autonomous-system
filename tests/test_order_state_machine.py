import pytest
from services.order_state_machine.models import OrderStatus
from services.order_state_machine.service import OrderState, transition
from services.order_state_machine.validator import InvalidOrderTransition

def test_valid_transition():
    state = transition(OrderState(OrderStatus.NEW), OrderStatus.VALIDATED)
    assert state.status is OrderStatus.VALIDATED

def test_invalid_transition_fails_closed():
    with pytest.raises(InvalidOrderTransition):
        transition(OrderState(OrderStatus.NEW), OrderStatus.DELIVERED)

def test_full_lifecycle():
    state = OrderState(OrderStatus.NEW)
    for target in (
        OrderStatus.VALIDATED, OrderStatus.ASSIGNED, OrderStatus.ROUTE_OPTIMIZED,
        OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED, OrderStatus.INVOICED,
        OrderStatus.CLOSED,
    ):
        state = transition(state, target)
    assert state.status is OrderStatus.CLOSED
