import re

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message
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
from SnackSack import db_logger
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
    p_input_order_number = State()

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

async def back_to_show_orders(call: CallbackQuery, state: FSMContext):
    await FSM.p_choose_order.set()
    await show_orders(call, state)


async def make_purchase(call: CallbackQuery, state: FSMContext):
    back_to_orders_markup = M.back_to_orders()
    # 1) Input order number
    edited_msg_text = re.sub(r'((\d+)-(\d+))', r'`\1`', call.message.text) # to keep markdown after editing message
    msg = await bot.edit_message_text(
            f"{edited_msg_text}\n\n*Введите номер заказа:*",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_to_orders_markup,
            parse_mode="markdown"
            )
    await FSM.p_input_order_number.set()

    async with state_proxy(dp) as storage:
        storage["prev_message"] = msg

    # 2) Log -> database logger that purchase has been made
    # 3) Delete order from orders
    pass


async def input_order_number(message: Message, state: FSMContext):
    back_to_orders_markup = M.back_to_orders()

    async with state.proxy() as storage:
        prev_message = storage["prev_message"]

    # Check if order number is correct
    if not re.match(r"((\d+)-(\d+))", message.text):
        msg = await bot.send_message(
                message.chat.id,
                "Некорректный ввод. Введите номер заказа:",
                reply_markup=back_to_orders_markup
                )

        await remove_markup(prev_message)
        await update_prev_message(msg, state)

        return -1 # XXX

    chat_id, random_number = map(int, message.text.split('-'))

    async with state_proxy(dp) as storage:
        orders_packages = storage["orders_packages"]

    found_order_packages = None
    found_order_fg = False
    for order_packages in orders_packages:
        order = order_packages["order"]

        if order.chat_id == chat_id and order.random_number == random_number:
            found_order_packages = order_packages
            found_order_fg = True
            break

    if not found_order_fg:
        msg = await bot.send_message(
                message.chat.id,
                "Заказ не найден.",
                reply_markup=back_to_orders_markup
                )

        await remove_markup(prev_message)
        await update_prev_message(msg, state)

        return -1 # XXX

    # Order is found at this point
    await delete_order(found_order_packages)

    msg = await bot.send_message(
            message.chat.id,
            "✅ Покупка завершена.",
            reply_markup=btmM.back()
            )

    await remove_markup(prev_message)
    await update_prev_message(msg, state)



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

async def remove_markup(message: Message):
    await bot.edit_message_text(
            message.text,
            message.chat.id,
            message.message_id,
            reply_markup=None
            )

async def update_prev_message(message: Message, state: FSMContext):
    async with state.proxy() as storage:
        storage["prev_message"] = message


async def delete_order(order_packages):
    order = order_packages["order"]

    db = await DBS.get_instance()
    await db.delete_order(order.id)

    packages = "\n\n".join([str(package) for package in order_packages["packages"]])
    log_message = f"💸\nСовершена покупка:\n- Номер заказа: {order.chat_id}-{order.random_number}\n- Состав:\n{packages}"

    db_logger.info(log_message)


class M:
    @staticmethod
    def back_to_orders():
        markup = IKM(row_width=1)

        markup.add(
                IKB("Назад", callback_data="cb_back_to_orders") # TODO -> MESSAGE; callbacks
                )

        return markup

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_orders" # XXX
    dp.register_callback_query_handler(pre_show_orders, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_order)
    register_back_to_menu_handler_from_new_state(dp, FSM.p_input_order_number)

    filter_ = lambda cb: cb.data == "cb_next_page"
    dp.register_callback_query_handler(next_page, filter_, state=FSM.p_choose_order)

    filter_ = lambda cb: cb.data == "cb_prev_page"
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.p_choose_order)

    filter_ = lambda cb: cb.data == "cb_make_purchase"
    dp.register_callback_query_handler(make_purchase, filter_, state=FSM.p_choose_order)

    dp.register_message_handler(input_order_number, lambda x: True, state=FSM.p_input_order_number)

    filter_ = lambda cb: cb.data == "cb_back_to_orders"
    dp.register_callback_query_handler(back_to_show_orders, filter_, state=FSM.p_input_order_number)
