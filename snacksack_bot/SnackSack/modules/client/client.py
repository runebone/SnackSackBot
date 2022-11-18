import re
import uuid
import random

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack import dp, bot
from SnackSack import DBS
from SnackSack import error
from SnackSack.messages import MSG
from SnackSack.database.tables import Packages, Stores, Addresses, Orders
from SnackSack.modules.utils import state_proxy
from SnackSack.modules.utils import ArrowsMarkup
from SnackSack.modules.utils import get_data_to_show_in_message
from SnackSack.modules.utils import get_client_partner_keyboard

# from SnackSack.modules.start import default

# TODO FIXME XXX: use choose_markup from utils
# MAX_N_OF_PACKAGES_ON_A_PAGE = 5

AM = ArrowsMarkup(
    "cb_back",
    "cb_prev_page",
    "cb_next_page",
    "c_choose_package"
)


class FSM(StatesGroup):
    c_choose_package = State()


# Message handlers
async def client(message: Message):
    db = await DBS.get_instance()
    packages = await db.get_all_packages()

    packages = list(filter(lambda x: x.amount > 0, packages))

    if len(packages) == 0:
        # TODO -> MESSAGE
        await message.answer("Пока пакетов нет. 📭")
        raise error.NoPackages(message)

    await FSM.c_choose_package.set()

    async with state_proxy(dp) as storage:
        storage["packages"] = packages
        storage["current_page"] = 1
        storage["packages_message"] = None
        storage["chosen_package_index"] = None
        storage["chosen_package_message_id"] = None

    await choose_package(message, dp.current_state())

async def choose_package(message: Message, state: FSMContext):
    async with state.proxy() as storage:
        packages = storage["packages"]
        current_page = storage["current_page"]

        markup = AM.choose_markup(current_page, len(packages))
        msg = await get_message_with_packages(current_page, packages)

        if storage["packages_message"] is None: # FIXME useless attribute
            packages_message = await message.answer(msg, reply_markup=markup)
            storage["packages_message"] = packages_message
        else: # FIXME aoaoao ugly if elses
            await bot.edit_message_text(
                msg,
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )

# Callback handlers
async def back(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        msg_id = storage["chosen_package_message_id"]
        if msg_id is not None:
            await bot.delete_message(call.message.chat.id, msg_id)

    await state.finish()
    await call.answer(MSG.EXITED_CHOOSE_PACKAGE_MODE)

    # keyboard = get_client_partner_keyboard()

    await bot.delete_message(call.message.chat.id, call.message.message_id)

    # await bot.send_message(
    #         call.message.chat.id,
    #         MSG.DEFAULT,
    #         reply_markup=keyboard
    #         )


async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1

    await choose_package(call.message, state)


async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1

    await choose_package(call.message, state)


# FIXME ugly; make the same logic in every module and abstract it out
async def choose_package_n(call: CallbackQuery, state: FSMContext):
    markup = M.confirm_cancel()

    async with state.proxy() as storage:
        n = int(re.findall(r"choose_package(\d+)", call.data)[0])

        chosen_package = storage["packages"][n - 1]

        db = await DBS.get_instance()

        chosen_package_address = await db.get_by_id(Addresses, chosen_package.address_id)

        chosen_package_store = await db.get_by_id(Stores, chosen_package_address.store_id)

        if storage["chosen_package_message_id"] is None:
            msg = await bot.send_message(
                call.message.chat.id,
                MSG.FMT_YOU_HAVE_CHOSEN_FULL.format(index=n, package=chosen_package, store=chosen_package_store, address=chosen_package_address),
                reply_markup=markup,
            )
            storage["chosen_package_message_id"] = msg.message_id
        else:
            await bot.edit_message_text(
                MSG.FMT_YOU_HAVE_CHOSEN_FULL.format(index=n, package=chosen_package, store=chosen_package_store, address=chosen_package_address),
                call.message.chat.id,
                storage["chosen_package_message_id"],
                reply_markup=markup,
                )

        storage["chosen_package_index"] = n - 1


async def cancel_order(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # XXX MESSAGE text not in messages
        msg_id = storage["chosen_package_message_id"]
        storage["chosen_package_message_id"] = None

        await bot.delete_message(call.message.chat.id, msg_id)

        # await bot.edit_message_text(
        #     f"🚫 {call.message.text}",
        #     call.message.chat.id,
        #     storage["chosen_package_message_id"],
        #     reply_markup=None,
        # )
        # await bot.edit_message_text(
        #     storage["packages_message"].text,
        #     storage["packages_message"].chat.id,
        #     storage["packages_message"].message_id,
        #     reply_markup=None,
        # )

    # await state.finish()


async def confirm_order(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # XXX MESSAGE text not in messages
        await bot.edit_message_text(
            f"✅ {call.message.text}",
            call.message.chat.id,
            storage["chosen_package_message_id"],
            reply_markup=None,
        )
        await bot.edit_message_text(
            storage["packages_message"].text,
            storage["packages_message"].chat.id,
            storage["packages_message"].message_id,
            reply_markup=None,
        )

    await create_order(call, state)

    # TODO (mb): payment

    await state.finish()

async def create_order(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    random_number = get_random_number(4)

    order = Orders.Record(uuid.uuid4(), call.message.chat.id, random_number)

    async with state.proxy() as storage:
        index = storage["chosen_package_index"]
        package = storage["packages"][index]

    await db.create_order(order, [package]) # FIXME only one package per order avaliable rn

    await db.decrement_package_amount(package.id)

    await call.answer("✅ Заказ успешно создан")

    await call.message.answer(f"🧾 Номер заказа: `{call.message.chat.id}-{random_number}`", parse_mode="markdown")

    # aoaoa
    # await default(call.message, state)
    # await state.finish()
    # await client(call.message)
    # await state.finish()


# Helpers

async def get_message_with_packages(page_number: int, packages: list[Packages.Record]) -> str:
    data = get_data_to_show_in_message(page_number, packages)

    db = await DBS.get_instance()

    # FIXME: log-level logic in high-level abstraction function
    message = []
    for d in data:
        package = d["record"]
        address = await db.get_by_id(Addresses, package.address_id)
        store = await db.get_by_id(Stores, address.store_id)
        message.append(MSG.FMT_PACKAGE_FULL.format(index=d["index"], package=package, address=address, store=store))

    message = "\n\n".join(message)

    return message

# def get_message_with_packages(page_number: int, packages: list[Packages.Record]) -> str:
#     i = 1
#     pn = page_number
#     message = []
#     N = MAX_N_OF_PACKAGES_ON_A_PAGE
#     for package in packages[N * (pn - 1) : N * pn]:
#         message.append(MSG.FMT_PACKAGE.format(index=(N * (pn - 1) + i), package=package))
#         i += 1

#     message = "\n\n".join(message)

#     return message

def get_random_number(number_of_digits: int) -> int:
    n = number_of_digits
    return random.randint(10 ** (n-1), 10 ** n)


# TODO: get most of markups from utils.M
# FIXME: row_width=MAX_N_OF_PACKAGES_ON_A_PAGE
class M:
    """Markups class."""

    @staticmethod
    def back_button(number_of_packages_on_page: int):
        markup = IKM(row_width=5)

        buttons = []
        for i in range(number_of_packages_on_page):
            buttons.append(IKB(f"{i+1}", callback_data=f"choose_package{i+1}"))
        markup.add(*buttons)

        markup.add(
            IKB(MSG.BTN_BACK, callback_data="cb_back"),
        )

        return markup

    @staticmethod
    def back_button_and_arrow_forward(number_of_packages_on_page: int):
        markup = IKM(row_width=5)

        buttons = []
        for i in range(number_of_packages_on_page):
            buttons.append(IKB(f"{i+1}", callback_data=f"choose_package{i+1}"))
        markup.add(*buttons)

        markup.add(
            IKB(MSG.BTN_BACK, callback_data="cb_back"),
            IKB(MSG.BTN_ARROW_FORWARD, callback_data="cb_next_page"),
        )

        return markup

    @staticmethod
    def both_arrows_and_back_button(number_of_packages_on_page: int):
        markup = IKM(row_width=5)

        buttons = []
        for i in range(number_of_packages_on_page):
            buttons.append(IKB(f"{i+1}", callback_data=f"choose_package{i+1}"))
        markup.add(*buttons)

        markup.add(
            IKB(MSG.BTN_ARROW_BACK, callback_data="cb_prev_page"),
            IKB(MSG.BTN_BACK, callback_data="cb_back"),
            IKB(MSG.BTN_ARROW_FORWARD, callback_data="cb_next_page"),
        )

        return markup

    @staticmethod
    def arrow_back_and_back_button(number_of_packages_on_page: int):
        markup = IKM(row_width=5)

        buttons = []
        for i in range(number_of_packages_on_page):
            buttons.append(IKB(f"{i+1}", callback_data=f"choose_package{i+1}"))
        markup.add(*buttons)

        markup.add(
            IKB(MSG.BTN_ARROW_BACK, callback_data="cb_prev_page"),
            IKB(MSG.BTN_BACK, callback_data="cb_back"),
        )

        return markup

    @staticmethod
    def confirm_cancel():
        markup = IKM(row_width=2)

        markup.add(
            IKB(MSG.BTN_CONFIRM, callback_data="cb_confirm"),
            IKB(MSG.BTN_CANCEL, callback_data="cb_cancel"),
        )

        return markup


# Setup handlers
def setup_handlers(dp: Dispatcher):
    dp.register_message_handler(client, text=MSG.BTN_CLIENT, state=None)

    filter_ = lambda cb: cb.data == "cb_back"
    dp.register_callback_query_handler(back, filter_, state=FSM.c_choose_package)

    filter_ = lambda cb: cb.data == "cb_next_page"
    dp.register_callback_query_handler(next_page, filter_, state=FSM.c_choose_package)

    filter_ = lambda cb: cb.data == "cb_prev_page"
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.c_choose_package)

    filter_ = lambda cb: cb.data == "cb_cancel"
    dp.register_callback_query_handler(cancel_order, filter_, state=FSM.c_choose_package)

    filter_ = lambda cb: cb.data == "cb_confirm"
    dp.register_callback_query_handler(confirm_order, filter_, state=FSM.c_choose_package)

    filter_ = lambda cb: re.match(r"c_choose_package(\d+)", cb.data)
    dp.register_callback_query_handler(choose_package_n, filter_, state=FSM.c_choose_package)
