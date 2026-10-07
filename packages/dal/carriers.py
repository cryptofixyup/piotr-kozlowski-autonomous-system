class CarriersDAL:
    def __init__(self, connection):
        self.connection = connection

    async def get_verified(self):
        return await self.connection.fetch(
            "SELECT * FROM carriers WHERE vat_verified = TRUE AND ocp_valid = TRUE ORDER BY rating DESC"
        )
