from .sql_query import SqlQuery


class BaseDB:
    def __init__(self, connection_pool):
        self.pool = connection_pool

    async def execute(self, sql_query: SqlQuery):
        async with self.pool.acquire() as con:
            await con.execute(*sql_query())

    async def fetch(self, sql_query: SqlQuery):
        async with self.pool.acquire() as con:
            return await con.fetch(*sql_query())
