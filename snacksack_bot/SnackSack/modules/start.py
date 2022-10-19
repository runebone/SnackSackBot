from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext

from SnackSack import bot, dp
from SnackSack.messages import MSG

from SnackSack.modules.utils import get_client_partner_keyboard


async def handle_start_cmd(message: types.Message, state: FSMContext):
    """Send starting message with reply keyboard to the user.

    Cancel any active states.
    """
    keyboard = get_client_partner_keyboard()
    await message.answer(MSG.START, reply_markup=keyboard)
    await state.finish()


async def default(message: types.Message, state: FSMContext):
    keyboard = get_client_partner_keyboard()

    # await bot.delete_message(message.chat.id, message.message_id)

    await bot.send_message(
            message.chat.id,
            MSG.DEFAULT,
            reply_markup=keyboard
            )


# Registering handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_start_cmd, commands=["start"], state="*")

    dp.register_message_handler(default, lambda x: True, state=None)
