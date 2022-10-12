import re

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
from SnackSack.database.tables import Packages
from SnackSack.modules.utils import state_proxy
from SnackSack.modules.utils import ArrowsMarkup

# TODO FIXME XXX: use choose_markup from utils
MAX_N_OF_PACKAGES_ON_A_PAGE = 5

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

    if len(packages) == 0:
        # TODO -> MESSAGE
        await message.answer("Пока пакетов нет. 📭")
        raise error.NoPackages(message)

    # markup = choose_markup(1, len(packages))
    markup = AM.choose_markup(1, len(packages))
    message_text = get_message_with_packages(1, packages)

    packages_message = await message.answer(message_text, reply_markup=markup)

    await FSM.c_choose_package.set()

    async with state_proxy(dp) as storage:
        storage["packages"] = packages
        storage["current_page"] = 1
        storage["packages_message"] = packages_message
        storage["chosen_package_index"] = None
        storage["chosen_package_message_id"] = None

# Callback handlers
async def back(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer(MSG.EXITED_CHOOSE_PACKAGE_MODE)
    await bot.edit_message_text(
        MSG.DEFAULT, call.message.chat.id, call.message.message_id, reply_markup=None
    )


async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1

        current_page = storage["current_page"]
        packages = storage["packages"]

        msg = get_message_with_packages(current_page, packages)
        # markup = choose_markup(current_page, len(packages))
        markup = AM.choose_markup(current_page, len(packages))

        storage["packages_message"] = await bot.edit_message_text(
            msg,
            call.message.chat.id,
            storage["packages_message"].message_id,
            reply_markup=markup,
        )


async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1

        current_page = storage["current_page"]
        packages = storage["packages"]

        msg = get_message_with_packages(current_page, packages)
        # markup = choose_markup(current_page, len(packages))
        markup = AM.choose_markup(current_page, len(packages))

        storage["packages_message"] = await bot.edit_message_text(
            msg,
            call.message.chat.id,
            storage["packages_message"].message_id,
            reply_markup=markup,
        )


async def choose_package_n(call: CallbackQuery, state: FSMContext):
    markup = M.confirm_cancel()

    async with state.proxy() as storage:
        n = int(re.findall(r"choose_package(\d+)", call.data)[0])

        chosen_package = storage["packages"][n - 1]

        if storage["chosen_package_message_id"] is None:
            msg = await bot.send_message(
                call.message.chat.id,
                MSG.FMT_YOU_HAVE_CHOSEN.format(index=n, package=chosen_package),
                reply_markup=markup,
            )
            storage["chosen_package_message_id"] = msg.message_id
        else:
            await bot.edit_message_text(
                MSG.FMT_YOU_HAVE_CHOSEN.format(index=n, package=chosen_package),
                call.message.chat.id,
                storage["chosen_package_message_id"],
                reply_markup=markup,
                )

        storage["chosen_package_index"] = n - 1


async def cancel_order(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        # XXX MESSAGE text not in messages
        await bot.edit_message_text(
            f"🚫 {call.message.text}",
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
    await state.finish()


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
        # TODO: payment
        # TODO: update number of packages in database or delete package
    await state.finish()


# Helpers
# def choose_markup(page_number: int, number_of_packages: int) -> IKM:
#     assert page_number > 0, "Invalid page number."
#     assert number_of_packages >= 0, "Invalid number of packages."

#     N = MAX_N_OF_PACKAGES_ON_A_PAGE

#     # n - number of packages on a page
#     n = min(N, number_of_packages - N * (page_number - 1))

#     if page_number == 1:
#         if N < number_of_packages:
#             return M.back_button_and_arrow_forward(n)
#         return M.back_button(n)

#     # page_number > 1
#     if page_number * N < number_of_packages:
#         return M.both_arrows_and_back_button(n)
#     return M.arrow_back_and_back_button(n)


def get_message_with_packages(page_number: int, packages: list[Packages.Record]) -> str:
    i = 1
    pn = page_number
    message = []
    N = MAX_N_OF_PACKAGES_ON_A_PAGE
    for package in packages[N * (pn - 1) : N * pn]:
        message.append(MSG.FMT_PACKAGE.format(index=(N * (pn - 1) + i), package=package))
        i += 1

    message = "\n\n".join(message)

    return message


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
