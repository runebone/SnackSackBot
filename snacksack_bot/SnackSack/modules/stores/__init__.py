from aiogram import Dispatcher

from . import products24

def setup_handlers(dp: Dispatcher):
    products24.setup_handlers(dp)
