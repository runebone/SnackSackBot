import asyncio

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncpg

from SnackSack import config
from SnackSack.logger import logger as bot_logger
from SnackSack.database.logger import logger as db_logger

from SnackSack.database.postgres import PostgresDB as DB

# Bot
bot = aiogram.Bot(token=config.BOT_TOKEN, parse_mode=aiogram.types.ParseMode.HTML)

# Dispatcher
storage = MemoryStorage()
loop = asyncio.get_event_loop()

dp = aiogram.Dispatcher(bot, storage=storage, loop=loop)

# Database
async def create_connection_pool():
    connection_pool = await asyncpg.create_pool(
        user=config.DB_USER,
        password=config.DB_PASS,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        min_size=1,
        max_size=10,
        max_inactive_connection_lifetime=300,
        command_timeout=30,
    )

    return connection_pool


# Database Singleton
class DBS:
    """Singleton, containing instance of database (which itself contains
    connection pool).
    """

    __instance = None

    @classmethod
    async def init(cls):
        if cls.__instance == None:
            cls.__instance = DB(await create_connection_pool())
        else:
            bot_logger.error("Attempt to initialize multiple instances of a Singleton.")

    @classmethod
    async def get_instance(cls):
        if cls.__instance == None:
            await cls.init()

        assert cls.__instance is not None, "Unable to get DB instance."

        return cls.__instance
