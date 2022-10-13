import re

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
from SnackSack.modules.utils import get_data_to_show_in_message
from SnackSack import error
from SnackSack.database.tables import Stores, Addresses
from SnackSack.modules.partner.utils import get_addresses_list, get_stores_list
from SnackSack.modules.partner.utils import M as puM

from .back_to_menu import register_back_to_menu_handler_from_new_state
from .back_to_menu import M as btmM
from .back_to_menu import cb_back_to_menu

from SnackSack.modules.utils import get_data_to_show_in_message


AM = ArrowsMarkup(
    "cb_back_to_stores", # FIXME DRY
    "cb_prev_page",
    "cb_next_page",
    "cb_store" # FIXME DRY
)


class FSM(StatesGroup):
    p_choose_store = State()
    p_choose_address = State()


# Callback query handlers
async def show_stores(call: CallbackQuery):
    addresses = await get_addresses_list(call.message.chat.id)
    stores = await get_stores_list(call.message.chat.id)

    if len(stores) == 0:
        await bot.edit_message_text(
            MSG.NO_STORES_YET,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=btmM.back()
        )
        raise error.PartnerNoStores(call.message)

    stores_names = [store.name for store in stores]

    markup = puM.stores(stores_names, "cb_store")

    await bot.edit_message_text(
        # TODO -> MESSAGE
        "🏡 Ваши магазины:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

    await FSM.p_choose_store.set()

    async with state_proxy(dp) as storage:
        storage["stores"] = stores
        storage["addresses"] = addresses
        storage["current_page"] = 1
        storage["chosen_store_index"] = None
        storage["chosen_store_addresses"] = None
        storage["chosen_address_index"] = None


async def choose_nth_store_address(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # 1) Get chosen store index
        if storage["chosen_store_index"] == None:
            store_index = int(re.findall(r"cb_store(\d+)", call.data)[0]) # FIXME: hardcoded cb_store
        else:
            store_index = storage["chosen_store_index"]

        # 2) Get list of store's addresses
        # // If there are stores - there must be at least one address per store
        stores = storage["stores"]
        addresses = storage["addresses"]

        store_addresses = [
            a for a in addresses if a.store_id == stores[store_index].id
        ]

        # 3) For each address, add its description to message to be sent
        msg = get_message_with_addresses(storage["current_page"], store_addresses)
        msg = "\n\n".join([f"Адреса {stores[store_index].name}:", msg])

        # 4) Get markup from AM.choose_markup
        markup = AM.choose_markup(storage["current_page"], len(store_addresses))

        markup.add(
            IKB("🏠 Добавить адрес", callback_data="cb_create_address") # TODO -> message; cb-> somewhere
        )

        # 5) After msg and markup are ready, edit current message with new data
        await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )

        storage["chosen_store_index"] = store_index
        storage["chosen_store_addresses"] = store_addresses

    await FSM.p_choose_address.set()

    async with state.proxy() as storage:
        storage["chosen_address_index"] = None

async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1
    await choose_nth_store_address(call, state)

async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1
    await choose_nth_store_address(call, state)

async def create_address(call: CallbackQuery, state: FSMContext):
    # XXX will be removed later
    async with state.proxy() as storage:
        store = storage["stores"][storage["chosen_store_index"]]
        address = await create_random_address(call.message.chat.id, store)

        addresses = await get_addresses_list(call.message.chat.id)
        storage["addresses"] = addresses

    await choose_nth_store_address(call, state)
    await call.answer(f"Создан случайный адрес: {address.address}")


# Helpers
def get_message_with_addresses(page_number: int, addresses: list[Addresses.Record]) -> str:
    data = get_data_to_show_in_message(page_number, addresses)

    message = []
    for d in data:
        message.append(MSG.FMT_ADDRESS.format(index=d["index"], address=d["record"]))

    message = "\n\n".join(message)

    return message

async def show_stores_and_finish_current_state(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await show_stores(call)


# XXX remove later
async def create_random_address(chat_id: int, store: Stores.Record):
    db = await DBS.get_instance()

    import uuid
    from SnackSack.database.tables import Addresses

    random_address = Addresses.Record(
        uuid.uuid4(),
        store.id,
        f"Random Demo Address [{str(uuid.uuid4()).split('-')[0]}]"
    )

    await db.create_address(chat_id, random_address)

    return random_address

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_shops" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(show_stores, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_store)

    filter_ = lambda cb: re.match(r"cb_store(\d+)", cb.data) # FIXME hardcode
    dp.register_callback_query_handler(choose_nth_store_address, filter_, state=FSM.p_choose_store)

    filter_ = lambda cb: cb.data == "cb_back_to_stores"
    dp.register_callback_query_handler(show_stores_and_finish_current_state, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_create_address"
    dp.register_callback_query_handler(create_address, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_next_page" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(next_page, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_prev_page" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.p_choose_address)
