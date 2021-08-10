import asyncpg
import logging

logger = logging.getLogger("root")


class Database:
    def __init__(self, user, password, host, database, port="5432"):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self._cursor = None

        self._connection_pool = None
        self.con = None

    async def connect(self):
        if not self._connection_pool:
            try:
                self._connection_pool = await asyncpg.create_pool(
                    min_size=1,
                    max_size=20,
                    command_timeout=60,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                )
                logger.info("Database pool connection opened")

            except Exception as e:
                logger.exception(e)

    async def fetch_rows(self, query: str, *args):
        if not self._connection_pool:
            await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            try:
                result = await self.con.fetch(query, *args)
                return result
            except Exception as e:
                logger.exception(e)
            finally:
                await self._connection_pool.release(self.con)

    async def execute(self, query: str, *args):
        if not self._connection_pool:
            await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            try:
                result = await self.con.execute(query, *args)
                return result
            except Exception as e:
                logger.exception(e)
            finally:
                await self._connection_pool.release(self.con)

    async def close(self):
        if not self._connection_pool:
            try:
                await self._connection_pool.close()
                logger.info("Database pool connection closed")
            except Exception as e:
                logger.exception(e)
