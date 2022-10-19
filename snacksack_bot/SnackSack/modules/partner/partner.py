import uuid
import datetime

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM
from SnackSack.modules.utils import get_client_partner_keyboard

from SnackSack import dp, bot
from SnackSack import DBS
from SnackSack.messages import MSG

import SnackSack.database.tables as t

from SnackSack.modules.utils import M as uM


# TODO: show "I'm partner" button only if user chat_id is in partners database

class FSM(StatesGroup):
    p_default = State()

# Message handlers
async def partner(message: Message):
    db = await DBS.get_instance()

    partners = await db.get_all_partners()
    partners_chat_ids = list(
        map(
            lambda x: x.chat_id,
            partners,
        )
    )

    # 1) Check if chat_id is in partner chat_ids
    if message.chat.id in partners_chat_ids:
        await FSM.p_default.set()
        # 2) If so, send him message with partner_menu markup
        await send_partner_menu(
            message.chat.id,
            MSG.FMT_DEMO_INITIAL_PARNTER_MENU.format(
                username=message.from_user.first_name
            ),
        )
    else:
        # 3) If it's not, in DEMO version, offer him to register as a partner
        # TODO: move to MESSAGE
        await send_partner_register_offer(
            message.chat.id,
            "Похоже вас нет в базе данных. Хотите стать партнёром?"
        )

# Callback query handlers
# XXX partially copy-pasted from prev version
async def demo_register_partner(call: CallbackQuery):
    await call.answer("✅")
    await bot.edit_message_text(
        call.message.text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )

    db = await DBS.get_instance()

    # random_id = str(uuid.uuid4()).split('-')[0]
    random_id = call.message.chat.first_name

    # 1) Add chat_id to database
    await call.answer("Добавляем вас в базу данных...")
    await db.create_partner(call.message.chat.id)

    # 2) Create some demo stores; single command to create demo store (2)
    await call.answer("Создаём демо-магазины...")
    demo_stores = [
        t.Stores.Record(uuid.uuid4(), f"[ДЕМО] Магазин 1 ({random_id})"),
        t.Stores.Record(uuid.uuid4(), f"[ДЕМО] Магазин 2 ({random_id})"),
    ]

    for store in demo_stores:
        await db.create_store(store)

    # 3) Create some demo addresses (2 for each store) (4)
    await call.answer("Создаём демо-адреса...")
    demo_addresses = [
        t.Addresses.Record(uuid.uuid4(), demo_stores[0].id, f"[ДЕМО] Адрес [М1] 1 ({random_id})"),
        t.Addresses.Record(uuid.uuid4(), demo_stores[0].id, f"[ДЕМО] Адрес [М1] 2 ({random_id})"),
        t.Addresses.Record(uuid.uuid4(), demo_stores[1].id, f"[ДЕМО] Адрес [М2] 1 ({random_id})"),
        t.Addresses.Record(uuid.uuid4(), demo_stores[1].id, f"[ДЕМО] Адрес [М2] 2 ({random_id})"),
    ]

    for address in demo_addresses:
        await db.create_address(call.message.chat.id, address)

    # 4) Create some demo packages (3)
    await call.answer("Создаём демо-пакеты...")
    now = datetime.datetime.now()

    demo_packages = [
        t.Packages.Record(
            uuid.uuid4(),
            demo_addresses[0].id,
            f"Хлеб, колбаса ({random_id})",
            datetime.datetime(now.year, now.month, now.day, 21, 0),
            1,
            300
        ),
        t.Packages.Record(
            uuid.uuid4(),
            demo_addresses[1].id,
            f"Молоко, хлопья ({random_id})",
            datetime.datetime(now.year, now.month, now.day, 22, 0),
            2,
            200
        ),
        t.Packages.Record(
            uuid.uuid4(),
            demo_addresses[2].id,
            f"Яйца ({random_id})",
            datetime.datetime(now.year, now.month, now.day, 23, 0),
            3,
            100
        )
    ]

    for package in demo_packages:
        await db.create_package(call.message.chat.id, package)

    await call.message.answer("✅ Вы успешно зарегистрированы в качестве партнёра.")
    await send_partner_menu(call.message.chat.id, "Меню:") # TODO -> MESSAGE
    await FSM.p_default.set()

# XXX mostly copy-pasted from prev version
async def demo_cancel_register_partner(call: CallbackQuery):
    await call.answer("❌")
    await bot.edit_message_text(
        call.message.text + " ❌",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )

async def back(call: CallbackQuery, state: FSMContext):
    await state.finish()

    keyboard = get_client_partner_keyboard()

    await bot.delete_message(call.message.chat.id, call.message.message_id)

    await bot.send_message(
            call.message.chat.id,
            MSG.DEFAULT,
            reply_markup=keyboard
            )

# Helpers
async def send_partner_menu(chat_id: int, message_text: str):
    markup = uM.partner_menu()

    await bot.send_message(chat_id, message_text, reply_markup=markup)

async def send_partner_register_offer(chat_id: int, message_text: str):
    markup = M.yes_no()

    await bot.send_message(chat_id, message_text, reply_markup=markup)

class M:
    """Markups class."""

    @staticmethod
    def yes_no():
        markup = IKM(row_width=2)
        markup.add(
            IKB("✅", callback_data="cb_yes"),
            IKB("❌", callback_data="cb_no"),
        )

        return markup

# Setup handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(partner, text=MSG.BTN_PARTNER, state=None)

    filter_ = lambda cb: cb.data == "cb_yes"
    dp.register_callback_query_handler(demo_register_partner, filter_, state=None)

    filter_ = lambda cb: cb.data == "cb_no"
    dp.register_callback_query_handler(demo_cancel_register_partner, filter_, state=None)

    filter_ = lambda cb: cb.data == "cb_back_to_choose_client_partner" # FIXME: DRY with utils.aoaoaooa callback
    dp.register_callback_query_handler(back, filter_, state=FSM.p_default)#None)
