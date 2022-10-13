# | -------------------------------- |
# | This is how the hell looks like. |
# | -------------------------------- |

import re
import uuid
import datetime

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
from SnackSack.modules.utils import M as uM

from SnackSack.modules.partner.utils import get_stores_list, get_addresses_list
from SnackSack.modules.partner.utils import M as puM

from .back_to_menu import register_back_to_menu_handler_from_new_state
from .back_to_menu import M as btmM

from SnackSack.database.tables import Packages

AM = ArrowsMarkup(
    "cb_back_to_choose_stores", # FIXME DRY; copy-pasted from stores
    "cb_prev_page",
    "cb_next_page",
    "cb_address" # FIXME
)

class FSM(StatesGroup):
    create_package = State()
    input_description = State()
    input_price = State()
    input_amount = State()
    input_time = State()
    final = State()

# CallbackQuery handlers
async def create_package(call: CallbackQuery):
    # 1) Choose store with buttons
    stores = await get_stores_list(call.message.chat.id)
    markup = puM.stores([s.name for s in stores], "store")

    await bot.edit_message_text(
            # TODO -> MESSAGE
            f"Выберите магазин:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
            )

    await FSM.create_package.set()
    async with state_proxy(dp) as storage:
        storage["current_page"] = 1
        storage["stores"] = stores
        storage["chosen_store_index"] = None
        storage["store_addresses"] = None
        storage["chosen_address_index"] = None

        storage["description"] = None
        storage["time"] = None
        storage["amount"] = None
        storage["price"] = None

        storage["desc_confirm_msg"] = None

        storage["package"] = None

    # 2) Choose address with 1 2 3 4 5 <- ->
    # 3) Input description
    # 4) Input pickup time
    # 5) Input price per package
    # 6) Input amount of packages available

async def choose_store(call: CallbackQuery, state: FSMContext):
    await FSM.create_package.set() # FIXME aoaoaaoaooa
    async with state.proxy() as storage:
        # 1) Get store index from callback
        if storage["chosen_store_index"] == None:
            store_index = int(re.findall(r"store(\d+)", call.data)[0])
            storage["chosen_store_index"] = store_index - 1 # DANGER - 1

    await pre_choose_address(call, state)


async def pre_choose_address(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        store_index = storage["chosen_store_index"]

        stores = storage["stores"]
        addresses = await get_addresses_list(call.message.chat.id)

        store_addresses = [
            a for a in addresses if a.store_id == stores[store_index].id
        ]

        data = get_data_to_show_in_message(storage["current_page"], store_addresses)

        msg = "\n\n".join(
            [f"{d['index']}. {d['record'].address}" for d in data]
        )
        # TODO -> MESSAGE of course
        msg = "\n\n".join([f"Выберите адрес <b>{stores[store_index].name}</b>:", msg])

        markup = AM.choose_markup(storage["current_page"], len(store_addresses))

        await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

        storage["store_addresses"] = store_addresses


async def choose_address(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # 1) Get chosen address index
        if storage["chosen_address_index"] == None:
            address_index = int(re.findall(r"cb_address(\d+)", call.data)[0])
            # 2) Remember it
            storage["chosen_address_index"] = address_index - 1 # DANGER - 1

    await pre_input_description(call, state)


async def pre_input_description(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # 3) Move to next stage (input package description)
        # FIXME: creating markups is a low-level logic; abstract them out;
        # don't mix abstraction levels; callback query handlers - one of the
        # highest levels of abstraction in bot
        markup = IKM(row_width=1)
        # FIXME: ugly... define all callbacks name in one place (mb on top)
        markup.add(
            IKB(
                MSG.BTN_BACK,
                callback_data=f"cb_back_to_choose_addresses_of_store{storage['chosen_store_index']}"
            )
        )

    # TODO -> MESSAGE
    msg = "Введите описание пакета (какие продукты в него входят):"

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
            )

    await FSM.input_description.set()


async def input_description(message: Message, state: FSMContext):
    # 1) Wait until user inputs description
    # 2) Show him what he has just input; show confirmation button; or, if he
    # inputs again, delete old message, send new one with confirmation
    await pre_confirm_description(message, state)


async def pre_confirm_description(message: Message, state: FSMContext):
    # Confirmation markup
    # FIXME: watch FIXME in prev func
    markup = IKM(row_width=1)
    markup.add(IKB("✅ Подтвердить", callback_data="cb_confim_description"))

    desc_confirm_msg = await message.answer(
            f"Описание:\n\n{message.text}",
            reply_markup=markup
            )

    async with state.proxy() as storage:
        if storage["desc_confirm_msg"] is not None:
            await bot.delete_message(
                message.chat.id,
                storage["desc_confirm_msg"].message_id
            )
        storage["desc_confirm_msg"] = desc_confirm_msg
        storage["description"] = message.text


async def confirm_description(call: CallbackQuery, state: FSMContext):
    await pre_input_price(call, state)

async def pre_input_price(call: CallbackQuery, state: FSMContext):
    markup = IKM(row_width=1)
    # FIXME: ugly... define all callbacks name in one place (mb on top)
    markup.add(
        IKB(
            MSG.BTN_BACK,
            callback_data=f"cb_back_to_input_description"
        )
    )

    await bot.edit_message_text(
            f"Введите цену, по которой собираетесь выставить пакет:", # TODO -> MESSAGE
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
            )
    await FSM.input_price.set()

async def input_price(message: Message, state: FSMContext):
    message_is_valid = bool(re.fullmatch(r"(\d+)", message.text.strip()))

    if not message_is_valid:
        await message.answer("Введите только цену, в рублях, цифрами:")
    else:
        # XXX: high cyclomatic complexity; ugly - remove else branch; exit if
        # 'if' statement executes mb; or set error_fg to True and assert
        # error_fg == False before continuing
        async with state.proxy() as storage:
            storage["price"] = int(message.text)

        await pre_input_amount(message, state)


async def pre_input_amount(message: Message, state: FSMContext):
    markup = IKM(row_width=1)
    # FIXME: ugly... define all callbacks name in one place (mb on top)
    markup.add(
        IKB(
            MSG.BTN_BACK,
            callback_data=f"cb_back_to_input_price"
        )
    )

    await message.answer("Введите, сколько таких пакетов с едой есть в наличии:", reply_markup=markup)
    await FSM.input_amount.set()

async def input_amount(message: Message, state: FSMContext):
    message_is_valid = bool(re.fullmatch(r"(\d+)", message.text.strip()))

    if not message_is_valid:
        await message.answer("Введите количество, числом:")
    else:
        # XXX: high cyclomatic complexity; ugly - remove else branch; exit if
        # 'if' statement executes mb; or set error_fg to True and assert
        # error_fg == False before continuing
        async with state.proxy() as storage:
            storage["amount"] = int(message.text)

        await pre_input_time(message, state)

async def pre_input_time(message: Message, state: FSMContext):
    markup = IKM(row_width=1)
    # FIXME: ugly... define all callbacks name in one place (mb on top)
    markup.add(
        IKB(
            MSG.BTN_BACK,
            callback_data=f"cb_back_to_input_amount"
        )
    )

    await message.answer("Введите, до какого времени сегодня пакет нужно забрать (в формате <b>HH:mm</b>):", reply_markup=markup)
    await FSM.input_time.set()

async def input_time(message: Message, state: FSMContext):
    message_is_valid = bool(re.fullmatch(r"(\d|[01]\d|2[0-3]):([0-5]\d)", message.text.strip()))

    if not message_is_valid:
        await message.answer("Введите время в формате <b>HH:mm</b> (23:00, 21:30...):")
    else:
        async with state.proxy() as storage:
            storage["time"] = message.text

        await FSM.final.set()
        await final(message, state)

async def final(message: Message, state: FSMContext):
    # 1) Show user what package will be created
    # 2) Confirm / Cancel buttons
    # 3) If confirm -> create Packages.Record; load it to database
    # 4) If cancel -> forget everything; finish state
    async with state.proxy() as storage:
        si = storage["chosen_store_index"]
        ai = storage["chosen_address_index"]
        msg = [
            "Итого:\n",
            f"Магазин: {storage['stores'][si].name}",
            f"Адрес: {storage['store_addresses'][ai].address}",
            f"Описание: {storage['description']}",
            f"Забрать до: {storage['time']}",
            f"Цена: {storage['price']}",
            f"Кол-во: {storage['amount']}"
        ]

    markup = IKM(row_width=2)

    markup.add(
            IKB("✅", callback_data="cb_final_confirm"),
            IKB("❌", callback_data="cb_final_cancel"),
            )

    msg = "\n".join(msg)

    await message.answer(msg, reply_markup=markup)

async def back_to_input_description(call: CallbackQuery, state: FSMContext):
    await choose_address(call, state)

async def back_to_input_price(call: CallbackQuery, state: FSMContext):
    await confirm_description(call, state)

async def back_to_input_amount(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        await pre_input_amount(call.message, state) # FIXME: bad logic; answering call message

async def back_to_input_time(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        await pre_input_time(call.message, state) # FIXME: bad logic; answering call message


async def final_confirm(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        ai = storage["chosen_address_index"]

        now = datetime.datetime.now()

        HH, mm = map(int, storage["time"].split(':'))

        pickup_before_dt = datetime.datetime(now.year, now.month, now.day, HH, mm)

        package = Packages.Record(
                uuid.uuid4(),
                storage["store_addresses"][ai].id,
                storage["description"],
                pickup_before_dt,
                int(storage["amount"]),
                int(storage["price"])
                )

    db = await DBS.get_instance()

    await db.create_package(call.message.chat.id, package)

    await bot.edit_message_text(
            f"{call.message.text}\n\n✅ Пакет успешно создан!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
            )
    await state.finish()

    await bot.send_message(
            call.message.chat.id,
            "Меню:", # TODO -> MESSAGE!!!
            reply_markup=uM.partner_menu()
            )

async def final_cancel(call: CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
            f"❌ {call.message.text}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
            )
    await state.finish()

    await bot.send_message(
            call.message.chat.id,
            "Меню:", # TODO -> MESSAGE!!!
            reply_markup=uM.partner_menu()
            )


async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1
    await pre_choose_address(call, state)

async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1
    await pre_choose_address(call, state)

# Helpers
class M:
    """Markups class."""
    pass

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_create_package" # FIXME hardcode
    dp.register_callback_query_handler(create_package, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.create_package)

    filter_ = lambda cb: re.match(r"store(\d+)", cb.data)
    dp.register_callback_query_handler(choose_store, filter_, state=FSM.create_package)

    filter_ = lambda cb: re.match(r"cb_back_to_choose_addresses_of_store(\d+)", cb.data)
    dp.register_callback_query_handler(choose_store, filter_, state=FSM.input_description)

    filter_ = lambda cb: cb.data == "cb_back_to_choose_stores"
    dp.register_callback_query_handler(create_package, filter_, state=FSM.create_package)

    filter_ = lambda cb: re.match(r"cb_address(\d+)", cb.data)
    dp.register_callback_query_handler(choose_address, filter_, state=FSM.create_package)

    dp.register_message_handler(input_description, lambda x: True, state=FSM.input_description)

    filter_ = lambda cb: cb.data == "cb_confim_description"
    dp.register_callback_query_handler(confirm_description, filter_, state=FSM.input_description)

    dp.register_message_handler(input_price, lambda x: True, state=FSM.input_price)

    dp.register_message_handler(input_amount, lambda x: True, state=FSM.input_amount)

    dp.register_message_handler(input_time, lambda x: True, state=FSM.input_time)

    filter_ = lambda cb: cb.data == "cb_back_to_input_description"
    dp.register_callback_query_handler(back_to_input_description, filter_, state=FSM.input_price)

    filter_ = lambda cb: cb.data == "cb_back_to_input_price"
    dp.register_callback_query_handler(back_to_input_price, filter_, state=FSM.input_amount)

    filter_ = lambda cb: cb.data == "cb_back_to_input_amount"
    dp.register_callback_query_handler(back_to_input_amount, filter_, state=FSM.input_time)

    filter_ = lambda cb: cb.data == "cb_back_to_input_time"
    dp.register_callback_query_handler(back_to_input_time, filter_, state=FSM.final)

    filter_ = lambda cb: cb.data == "cb_final_confirm"
    dp.register_callback_query_handler(final_confirm, filter_, state=FSM.final)

    filter_ = lambda cb: cb.data == "cb_final_cancel"
    dp.register_callback_query_handler(final_cancel, filter_, state=FSM.final)

    filter_ = lambda cb: cb.data == "cb_prev_page"
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.create_package)

    filter_ = lambda cb: cb.data == "cb_next_page"
    dp.register_callback_query_handler(next_page, filter_, state=FSM.create_package)
