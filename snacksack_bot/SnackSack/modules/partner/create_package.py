from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack.messages import MSG
from SnackSack import dp, bot
from SnackSack import DBS
import SnackSack.database.tables as t
from SnackSack.modules.utils import state_proxy
from SnackSack.modules.utils import ArrowsMarkup

from .back_to_menu import register_back_to_menu_handler_from_new_state
from .back_to_menu import M as btmM


class FSM(StatesGroup):
    create_package = State()
    input_description = State()
    input_time = State()
    input_number_of_packages = State()
    input_price = State()
    final = State()

# Helpers
class M:
    """Markups class."""
    pass

# Setup handlers
def setup_handlers(dp: Dispatcher):
    pass
