from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from SnackSack import bot, dp
from SnackSack import DBS

from SnackSack.messages import MSG

from SnackSack.modules.partner.utils import register_partner

class FSM(StatesGroup):
    p_default = State()

async def register(message: types.Message):
    db = await DBS.get_instance()

    partners = await db.get_all_partners()
    partners_chat_ids = list(
        map(
            lambda x: x.chat_id,
            partners,
        )
    )

    if (message.chat.id in partners_chat_ids):
        await message.answer("Вы уже зарегистрированы в качестве партнёра.")
    else:
        await register_partner(
            message.chat.id,
            "Продукты 24",
            "Бакунинская улица, 4с3"
        )

        await message.answer("Вы успешно добавлены в список партнёров.")

        from SnackSack.modules.utils import M as uM
        markup = uM.partner_menu()
        await message.answer("Меню:", reply_markup=markup)
        await FSM.p_default.set()


# Registering handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(register, commands=["products24"], state=None)
