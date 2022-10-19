import re
from uuid import uuid4

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message
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
    "cb_address" # FIXME DRY
)


class FSM(StatesGroup):
    p_choose_store = State()
    p_choose_address = State()
    p_input_address = State()


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

        storage["addresses"] = store_addresses

        # 3) For each address, add its description to message to be sent
        msg = get_message_with_addresses(storage["current_page"], store_addresses)
        msg = "\n\n".join([f"Адреса {stores[store_index].name}:", msg])

        # 4) Get markup from AM.choose_markup
        markup = AM.choose_markup(storage["current_page"], len(store_addresses))

        markup.add(
            IKB("🏠 Добавить адрес", callback_data="cb_create_address") # TODO -> message; cb-> somewhere
        )

        # from SnackSack import bot_logger
        # bot_logger.debug(markup)
        markup["inline_keyboard"].insert(1, markup["inline_keyboard"].pop())

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

    # TODO: remove if nothing breaks
    # async with state.proxy() as storage:
    #     storage["chosen_address_index"] = None

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


async def choose_address(call: CallbackQuery, state: FSMContext):
    # 1) Show address with Back / Delete address markup
    async with state.proxy() as storage:
        match_ = re.findall(r"cb_address(\d+)", call.data)

        if match_ != []:
            n = int(match_[0])
            i = n - 1
            storage["chosen_address_index"] = i
        else:
            i = storage["chosen_address_index"]
        address = storage["addresses"][i]

    msg = await get_message_with_full_address_info(i, address)

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.address()
            )

async def back_to_addresses(call: CallbackQuery, state: FSMContext):
    await choose_nth_store_address(call, state)

# FIXME AOAOAOAAOOAOOAOAAOOAAAOOAAAOOAOAOAOAOAOAAOAOOAOAAOOOAOAAA
async def delete_address(call: CallbackQuery, state: FSMContext):
    # 1) Get all things which will be "CASCADEly" deleted with address (packages, orders)
    async with state.proxy() as storage:
        i = storage["chosen_address_index"]
        address = storage["addresses"][i]

    db = await DBS.get_instance()

    packages = await db.get_packages_by_address(address.id)
    orders = []

    for package in packages:
        orders_ = await db.get_orders_by_package(package.id)
        for order in orders_:
            orders.append(order)

    i = 1
    msg = []
    for package in packages:
        msg.append(MSG.FMT_PACKAGE.format(index=f"<b>Пакет {i}</b>", package=package))
        i += 1

    if orders != []:
        i = 1

    for order in orders:
        order_number = f"{order.chat_id}-{order.random_number}" # FIXME hardcoded order number structure
        # order_body = MSG.FMT_ORDER_BODY.format(description=order.description, price=order.price)

        msg.append(f"<b>Заказ {i}</b>. {order_number}")#\n{order_body}")
        i += 1

    msg = "\n\n".join(msg)

    ending = f"Вы уверены, что хотите удалить <b>{address.address}</b>?"
    if packages == []:
        msg = ending
    else:
        msg = f"❗<b>ВНИМАНИЕ</b>❗\n\nВместе с адресом будут удалены следующие пакеты и заказы:\n\n{msg}\n\n{ending}"


    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.confirm_cancel_delete()
            )

async def cancel_delete(call: CallbackQuery, state: FSMContext):
    await choose_address(call, state)
    # await back_to_addresses(call, state)

async def confirm_delete(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state.proxy() as storage:
        i = storage["chosen_address_index"]
        address = storage["addresses"][i]

        await db.delete_address(address.id)

        addresses = await get_addresses_list(call.message.chat.id)
        storage["addresses"] = addresses

    await call.answer("✅ Адрес успешно удалён.")

    await back_to_addresses(call, state)

async def input_address_again(call: CallbackQuery, state: FSMContext):
    await pre_input_address(call, state, M.confirm_update_address())

async def input_new_address(call: CallbackQuery, state: FSMContext):
    await pre_input_address(call, state, M.confirm_new_address())

async def pre_input_address(call: CallbackQuery, state: FSMContext, confirm_address_markup: IKM):
    await bot.edit_message_text(
            "Введите адрес:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.back_to_addresses()
            )
    await FSM.p_input_address.set()

    async with state_proxy(dp) as storage:
        storage["new_address_str"] = None
        storage["prev_confirm_address_msg"] = None
        storage["confirm_address_markup"] = confirm_address_markup


async def input_address(message: Message, state: FSMContext):
    async with state_proxy(dp) as storage:
        if storage["prev_confirm_address_msg"] is not None:
            prev_message = storage["prev_confirm_address_msg"]
            await bot.delete_message(prev_message.chat.id, prev_message.message_id)

        markup = storage["confirm_address_markup"]

        msg = await bot.send_message(message.chat.id, f"Адрес:\n\n{message.text}", reply_markup=markup)

        storage["prev_confirm_address_msg"] = msg
        storage["new_address_str"] = message.text

async def confirm_address_update_chosen(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state_proxy(dp) as storage:
        new_address_str = storage["new_address_str"]
        i = storage["chosen_address_index"]
        address = storage["addresses"][i]

        await db.update_address(address.id, new_address_str)

        storage["addresses"][i] = await db.get_by_id(Addresses, address.id) # XXX aoaoao

    await call.answer("✅ Адрес успешно обновлён.")

    await FSM.p_choose_address.set()
    # await choose_address(call, state)
    await back_to_addresses(call, state)


async def confirm_address_input_new(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state_proxy(dp) as storage:
        new_address_str = storage["new_address_str"]

        i = storage["chosen_store_index"]
        store = storage["stores"][i]

        new_address = Addresses.Record(uuid4(), store.id, new_address_str)

        storage["addresses"].append(new_address)

    await db.create_address(call.message.chat.id, new_address)

    await call.answer("✅ Адрес успешно создан.")

    await FSM.p_choose_address.set()

    await back_to_addresses(call, state)


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


async def get_message_with_full_address_info(index: int, address: Addresses.Record):
    db = await DBS.get_instance()

    store = await db.get_by_id(Stores, address.store_id)

    msg = f"Магазин: {store.name}\nАдрес: {address.address}"

    msg = "\n\n".join([f"Вы выбрали {index+1}.", msg])

    return msg

class M:
    @staticmethod
    def back_to_addresses():
        markup = IKM(row_width=1)

        markup.add(
                IKB("Назад", callback_data="cb_back_to_addresses"),
                )

        return markup

    @staticmethod
    def address():
        markup = IKM(row_width=1)

        markup.add(
                IKB("🔁 Ввести заново", callback_data="cb_input_address_again"),
                IKB("🗑️ Удалить адрес", callback_data="cb_delete_address"),
                IKB("Назад", callback_data="cb_back_to_addresses"),
                )

        return markup

    @staticmethod
    def confirm_cancel_delete():
        markup = IKM(row_width=2)

        markup.add(
                IKB("✅", callback_data="cb_confirm_delete"),
                IKB("❌", callback_data="cb_cancel_delete")
                )

        return markup

    @staticmethod
    def confirm_update_address():
        markup = IKM(row_width=1)
        markup.add(
                IKB("Подтвердить ✅", callback_data="cb_confirm_update_address"),
                )
        return markup

    @staticmethod
    def confirm_new_address():
        markup = IKM(row_width=1)
        markup.add(
                IKB("Подтвердить ✅", callback_data="cb_confirm_new_address"),
                )
        return markup


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

from SnackSack.modules.partner.partner import FSM as pFSM

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_shops" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(show_stores, filter_, state=pFSM.p_default)#None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_store)

    filter_ = lambda cb: re.match(r"cb_store(\d+)", cb.data) # FIXME hardcode
    dp.register_callback_query_handler(choose_nth_store_address, filter_, state=FSM.p_choose_store)

    filter_ = lambda cb: cb.data == "cb_back_to_stores"
    dp.register_callback_query_handler(show_stores_and_finish_current_state, filter_, state=FSM.p_choose_address)

    # filter_ = lambda cb: cb.data == "cb_create_address"
    # dp.register_callback_query_handler(create_address, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_next_page" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(next_page, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_prev_page" # FIXME: hardcode, very complex logic
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: re.match(r"cb_address(\d+)", cb.data) # FIXME hardcode
    dp.register_callback_query_handler(choose_address, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_back_to_addresses"
    dp.register_callback_query_handler(back_to_addresses, filter_, state=FSM.p_choose_address)
    dp.register_callback_query_handler(back_to_addresses, filter_, state=FSM.p_input_address)

    filter_ = lambda cb: cb.data == "cb_delete_address"
    dp.register_callback_query_handler(delete_address, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_cancel_delete"
    dp.register_callback_query_handler(cancel_delete, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_confirm_delete"
    dp.register_callback_query_handler(confirm_delete, filter_, state=FSM.p_choose_address)

    filter_ = lambda cb: cb.data == "cb_input_address_again"
    dp.register_callback_query_handler(input_address_again, filter_, state=FSM.p_choose_address)

    dp.register_message_handler(input_address, lambda x: True, state=FSM.p_input_address)

    filter_ = lambda cb: cb.data == "cb_confirm_update_address"
    dp.register_callback_query_handler(confirm_address_update_chosen, filter_, state=FSM.p_input_address)

    filter_ = lambda cb: cb.data == "cb_confirm_new_address"
    dp.register_callback_query_handler(confirm_address_input_new, filter_, state=FSM.p_input_address)

    filter_ = lambda cb: cb.data == "cb_create_address"
    dp.register_callback_query_handler(input_new_address, filter_, state=FSM.p_choose_address)
