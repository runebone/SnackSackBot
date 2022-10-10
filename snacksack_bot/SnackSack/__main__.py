from aiogram import executor

import SnackSack
from SnackSack import dp
from SnackSack import DBS
from SnackSack import bot_logger
from SnackSack import modules


async def on_startup(_):
    await DBS.init()

    modules.client.setup_handlers(dp)


async def on_shutdown(_):
    pass


if __name__ == "__main__":
    executor.start_polling(
        dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown
    )
