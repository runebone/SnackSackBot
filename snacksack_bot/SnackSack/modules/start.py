from aiogram import types
from aiogram import Dispatcher
from aiogram.types.reply_keyboard import KeyboardButton as KB
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup as RKM
from aiogram.dispatcher import FSMContext

from SnackSack import dp
from SnackSack.messages import MSG


def get_client_partner_keyboard() -> RKM:
    client_button = KB(text=MSG.BTN_CLIENT)
    partner_button = KB(text=MSG.BTN_PARTNER)

    keyboard = RKM(resize_keyboard=True, one_time_keyboard=True)
    keyboard = keyboard.row(client_button, partner_button)

    return keyboard


async def handle_start_cmd(message: types.Message, state: FSMContext):
    """Send starting message with reply keyboard to the user.

    Cancel any active states.
    """
    keyboard = get_client_partner_keyboard()
    await message.answer(MSG.START, reply_markup=keyboard)
    await state.finish()


# Registering handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_start_cmd, commands=["start"], state="*")
