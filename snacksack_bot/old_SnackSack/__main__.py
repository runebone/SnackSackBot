from aiogram import executor

from SnackSack import dp
from SnackSack import handlers


async def on_startup(_):
    pass


async def on_shutdown(_):
    pass


if __name__ == "__main__":
    executor.start_polling(
        dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown
    )
