class KPIsDAL:
    def __init__(self, connection):
        self.connection = connection

    async def record(self, name, value, metadata=None):
        return await self.connection.fetchrow(
            """INSERT INTO kpis (name, value, metadata)
               VALUES ($1, $2, $3)
               RETURNING *""",
            name, value, metadata or {},
        )
