from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext

from SnackSack import bot, dp, DBS
from SnackSack.messages import MSG

from SnackSack.modules.utils import get_client_partner_keyboard

from SnackSack.modules.client.client import client

async def handle_start_cmd(message: types.Message, state: FSMContext):
    """Send starting message with reply keyboard to the user.

    Cancel any active states.
    """
    db = await DBS.get_instance()

    partners = await db.get_all_partners()
    partners_chat_ids = list(
        map(
            lambda x: x.chat_id,
            partners,
        )
    )

    if (message.chat.id in partners_chat_ids):
        keyboard = get_client_partner_keyboard()
        await message.answer(MSG.START, reply_markup=keyboard)
    else:
        await message.answer(MSG.CLIENT_START)

    await state.finish()


async def default(message: types.Message):
    db = await DBS.get_instance()

    partners = await db.get_all_partners()
    partners_chat_ids = list(
        map(
            lambda x: x.chat_id,
            partners,
        )
    )

    if (message.chat.id in partners_chat_ids):
        keyboard = get_client_partner_keyboard()

        # await bot.delete_message(message.chat.id, message.message_id)

        await bot.send_message(
                message.chat.id,
                MSG.DEFAULT,
                reply_markup=keyboard
                )
    else:
        await client(message)


# Registering handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_start_cmd, commands=["start"], state="*")

    dp.register_message_handler(default, lambda x: True, state=None)
