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
from SnackSack import error
from SnackSack.database.tables import Stores

from .back_to_menu import register_back_to_menu_handler_from_new_state
from .back_to_menu import M as btmM
from .back_to_menu import cb_back_to_menu


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
    db = await DBS.get_instance()

    addresses = await db.get_partner_addresses(call.message.chat.id)

    stores = []
    stores_names = []
    for address in addresses:
        # FIXME: extra work, not very effective
        store = await db.get_by_id(Stores, address.store_id)

        if store.name not in stores_names:
            stores_names.append(store.name)
            stores.append(store)

    if len(stores_names) == 0:
        await bot.edit_message_text(
            MSG.NO_STORES_YET,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=btmM.back()
        )
        raise error.PartnerNoStores(call.message)

    markup = M.my_stores(stores_names)

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
        storage["chosen_address_index"] = None


async def choose_store_n(call: CallbackQuery, state: FSMContext):
    # 1) Get chosen store index
    store_index = int(re.findall(r"cb_store(\d+)", call.data)[0]) # FIXME: hardcoded cb_store

    async with state.proxy() as storage:
        # 2) Get list of store's addresses
        # // If there are stores - there must be at least one address per store
        stores = storage["stores"]
        addresses = storage["addresses"]

        store_addresses = [
            a for a in addresses if a.store_id == stores[store_index].id
        ]

        # 3) For each address, add its description to message to be sent
        i = 0
        msg = [f"Адреса {stores[store_index].name}:"] # TODO -> MESSAGE
        for sa in store_addresses:
            msg.append(f"{i+1}. {sa.address}")
            i += 1
        msg = "\n\n".join(msg)

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

    await FSM.p_choose_address.set()

    async with state.proxy() as storage:
        storage["chosen_address_index"] = None


async def create_address(call: CallbackQuery, state: FSMContext):
    pass


# Helpers
class M:
    """Markups class."""
    @staticmethod
    def my_stores(stores_names: list[str]):
        markup = IKM(row_width=1)

        i = 0
        for store_name in stores_names:
            markup.add(
                IKB(f"{store_name}", callback_data=f"cb_store{i}") # TODO add callback name to somewhere to store it in an organized way
            )
            i += 1

        markup.add(IKB(MSG.BTN_BACK, callback_data=cb_back_to_menu)) # FIXME UGLY

        return markup

async def show_stores_and_finish_current_state(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await show_stores(call)

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_shops" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(show_stores, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_store)

    filter_ = lambda cb: re.match(r"cb_store(\d+)", cb.data) # FIXME hardcode
    dp.register_callback_query_handler(choose_store_n, filter_, state=FSM.p_choose_store)

    filter_ = lambda cb: cb.data == "cb_back_to_stores"
    dp.register_callback_query_handler(show_stores_and_finish_current_state, filter_, state=FSM.p_choose_address)
