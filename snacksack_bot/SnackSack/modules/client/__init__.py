from aiogram import Dispatcher

from . import client

def setup_handlers(dp: Dispatcher):
    client.setup_handlers(dp)
