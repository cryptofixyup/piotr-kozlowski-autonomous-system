class AssignmentsDAL:
    def __init__(self, connection):
        self.connection = connection

    async def create(self, order_id, vehicle_id, carrier_id, confidence):
        return await self.connection.fetchrow(
            """INSERT INTO assignments
               (order_id, vehicle_id, carrier_id, confidence)
               VALUES ($1, $2, $3, $4)
               RETURNING *""",
            order_id, vehicle_id, carrier_id, confidence,
        )
