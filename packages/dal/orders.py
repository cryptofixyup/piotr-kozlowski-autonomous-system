from dataclasses import dataclass
from uuid import UUID
from services.order_state_machine.models import OrderStatus

@dataclass(frozen=True, slots=True)
class OrderRecord:
    id: UUID
    status: OrderStatus

class OrdersDAL:
    def __init__(self, connection):
        self.connection = connection

    async def get_new_orders(self):
        return await self.connection.fetch(
            "SELECT id, status FROM orders WHERE status = $1 ORDER BY created_at",
            OrderStatus.NEW.value,
        )

    async def update_status(self, order_id: UUID, status: OrderStatus) -> None:
        await self.connection.execute(
            "UPDATE orders SET status = $1, updated_at = NOW() WHERE id = $2",
            status.value,
            order_id,
        )
