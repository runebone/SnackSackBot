import sqlite3
import asyncio

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncpg

from SnackSack import config
from SnackSack.logger import logger as bot_logger
from SnackSack.database.logger import logger as db_logger

# Bot
bot = aiogram.Bot(token=config.BOT_TOKEN, parse_mode=aiogram.types.ParseMode.HTML)

# Dispatcher
storage = MemoryStorage()
loop = asyncio.get_event_loop()

dp = aiogram.Dispatcher(bot, storage=storage, loop=loop)

# Database

# REMOVEME
# db = {
#     "partner": database.PartnerDB("SnackSack/database/partners.json"),
#     "package": database.PackageDB("SnackSack/database/packages.json"),
# }

# REMOVEME
# from SnackSack.database import SQLiteDB
# con = sqlite3.connect(SQLITE_DB_PATH)
# db = SQLiteDB(con)

# TODO: connection pool
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
