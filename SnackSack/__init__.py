# Bot
from SnackSack import config
import aiogram

bot = aiogram.Bot(
        token=config.BOT_TOKEN,
        parse_mode=aiogram.types.ParseMode.HTML
        )

# Dispatcher
import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()
loop = asyncio.get_event_loop()

dp = aiogram.Dispatcher(bot, storage=storage, loop=loop)

# Database
from SnackSack import database

db = {
        "partner": database.PartnerDB("SnackSack/database/partners.json"),
        "package": database.PackageDB("SnackSack/database/packages.json")
        }
