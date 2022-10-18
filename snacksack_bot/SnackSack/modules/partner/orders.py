from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack.modules.utils import ArrowsMarkup
from SnackSack.modules.utils import get_data_to_show_in_message
from SnackSack.modules.partner.back_to_menu import register_back_to_menu_handler_from_new_state

from SnackSack import bot, dp
from SnackSack import DBS
from SnackSack import error
from SnackSack.messages import MSG
from SnackSack.database.tables import Orders, OrderPackages, Packages

from SnackSack.modules.partner.back_to_menu import M as btmM

from SnackSack.modules.utils import state_proxy

AM = ArrowsMarkup(
    "cb_back_to_menu", # FIXME DRY; copy-pasted from stores
    "cb_prev_page",
    "cb_next_page",
    None,
    False
)

class FSM(StatesGroup):
    p_choose_order = State()

# FIXME confusing function names
async def pre_show_orders(call: CallbackQuery, state: FSMContext):
    # 1) Get orders' packages list from database
    orders_packages = await get_orders_packages_list(call.message.chat.id)

    if len(orders_packages) == 0:
        await bot.edit_message_text(
            MSG.NO_ORDERS_YET,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=btmM.back()
        )
        raise error.PartnerNoStores(call.message)

    await FSM.p_choose_order.set()

    async with state_proxy(dp) as storage:
        storage["current_page"] = 1
        storage["orders_packages"] = orders_packages

    await show_orders(call, state)

async def show_orders(call: CallbackQuery, state: FSMContext):
    async with state_proxy(dp) as storage:
        current_page = storage["current_page"]
        orders_packages = storage["orders_packages"]

    # 2) Choose markup
    markup = AM.choose_markup(current_page, len(orders_packages))

    data = get_data_to_show_in_message(current_page, orders_packages)

    msg = []
    for d in data:
        order_number = "{chat_id}-{number}".format(
                chat_id=d["record"]["order"].chat_id,
                number=d["record"]["order"].random_number
                )

        order_msg_head = MSG.FMT_ORDER_HEADER.format(
                    order_number=order_number
                    )

        order_msg_body = []

        packages = d["record"]["packages"]
        for package in packages:
            order_msg_body.append(
                    MSG.FMT_ORDER_BODY.format(
                        description=package.description,
                        price=package.price
                        )
                    )

        order_msg_body = "\n\n".join(order_msg_body)
        order_msg = f"{order_msg_head}\n{order_msg_body}"

        msg.append(order_msg)
    msg = "\n\n".join(msg)

    # FIXME shifted abstraction level

    markup.add(
            IKB("Провести покупку", callback_data="cb_make_purchase") # TODO -> MESSAGE; cb -> somewhere
            )

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='markdown'
            )

    # await state.finish() # FIXME STOPPED HERE

# Callback query handlers
async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1

    await show_orders(call, state)


async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1

    await show_orders(call, state)

# Helpers
async def get_orders_packages_list(chat_id: int):
    db = await DBS.get_instance()

    orders = await db.get_partner_orders(chat_id)

    orders_packages_list = []
    for order in orders:
        order_packages = await db.get_order_packages(order.id)

        orders_packages_list.append({
            "order": order,
            "packages": order_packages
            })

    return orders_packages_list

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_orders" # XXX
    dp.register_callback_query_handler(pre_show_orders, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_order)

    filter_ = lambda cb: cb.data == "cb_next_page"
    dp.register_callback_query_handler(next_page, filter_, state=FSM.p_choose_order)

    filter_ = lambda cb: cb.data == "cb_prev_page"
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.p_choose_order)
