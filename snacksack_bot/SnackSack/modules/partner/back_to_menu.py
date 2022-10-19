from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State

from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack import bot
from SnackSack.messages import MSG
from SnackSack.modules.utils import M as uM

# FIXME: very ugly organization

cb_back_to_menu = "cb_back_to_menu"

from SnackSack.modules.partner.partner import FSM as pFSM

async def back_to_menu(call: CallbackQuery, state: FSMContext):
    # TODO: -> MESSAGE
    await bot.edit_message_text(
        "Меню:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=uM.partner_menu()
    )

    if state is not None:
        await state.finish()
        await pFSM.p_default.set()


class M:
    """Markups class."""

    @staticmethod
    def back():
        markup = IKM(row_width=1)
        markup.add(
            IKB(MSG.BTN_BACK, callback_data=cb_back_to_menu),
        )

        return markup


def register_back_to_menu_handler_from_new_state(dp: Dispatcher, state: State | None):
    filter_ = lambda cb: cb.data == cb_back_to_menu
    dp.register_callback_query_handler(back_to_menu, filter_, state=state)


def setup_handlers(dp: Dispatcher):
    # register_back_to_menu_handler_from_new_state(dp, None)
    register_back_to_menu_handler_from_new_state(dp, pFSM.p_default)
