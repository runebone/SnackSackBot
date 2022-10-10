import re

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack import dp, bot
from SnackSack import DBS
from SnackSack.messages import MSG


class FSM(StatesGroup):
    create_partner = State()

    create_package = State()
    input_description = State()
    input_time = State()
    input_number_of_packages = State()
    input_price = State()
    final = State()


# Message handlers
async def partner(message: Message):
    pass

# Callback query handlers
pass

# Helpers
pass

# Setup handlers
def setup_handlers(dp: Dispatcher):
    pass
