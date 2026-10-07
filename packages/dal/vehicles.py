class VehiclesDAL:
    def __init__(self, connection):
        self.connection = connection

    async def get_available(self):
        return await self.connection.fetch(
            "SELECT * FROM vehicles WHERE available = TRUE ORDER BY registration"
        )
