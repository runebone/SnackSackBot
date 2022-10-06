import asyncio

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from SnackSack import config
from SnackSack import database

# Bot
bot = aiogram.Bot(token=config.BOT_TOKEN, parse_mode=aiogram.types.ParseMode.HTML)

# Dispatcher
storage = MemoryStorage()
loop = asyncio.get_event_loop()

dp = aiogram.Dispatcher(bot, storage=storage, loop=loop)

# Database
db = {
    "partner": database.PartnerDB("SnackSack/database/partners.json"),
    "package": database.PackageDB("SnackSack/database/packages.json"),
}
