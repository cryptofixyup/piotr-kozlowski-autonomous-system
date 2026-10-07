from .models import OrderStatus

ALLOWED_TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.NEW: (OrderStatus.VALIDATED,),
    OrderStatus.VALIDATED: (OrderStatus.ASSIGNED,),
    OrderStatus.ASSIGNED: (OrderStatus.ROUTE_OPTIMIZED,),
    OrderStatus.ROUTE_OPTIMIZED: (OrderStatus.IN_TRANSIT,),
    OrderStatus.IN_TRANSIT: (OrderStatus.DELIVERED,),
    OrderStatus.DELIVERED: (OrderStatus.INVOICED,),
    OrderStatus.INVOICED: (OrderStatus.CLOSED,),
}
