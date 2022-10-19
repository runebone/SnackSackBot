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
from SnackSack.modules.utils import M as uM
from SnackSack import error

from .back_to_menu import register_back_to_menu_handler_from_new_state
from .back_to_menu import M as btmM

from SnackSack.modules.utils import get_data_to_show_in_message
from SnackSack.database.tables import Packages, Addresses, Stores

AM = ArrowsMarkup(
    "cb_back_to_menu", # FIXME DRY
    "cb_prev_page",
    "cb_next_page",
    "cb_choose"
)

class FSM(StatesGroup):
    p_choose_package = State()

# Callback query handlers
async def show_packages(call: CallbackQuery):
    db = await DBS.get_instance()

    packages = await db.get_partner_packages(call.message.chat.id)

    if len(packages) == 0:
        await bot.edit_message_text(
            MSG.NO_PACKAGES_YET,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=btmM.back()
        )
        raise error.PartnerNoPackages(call.message)

    # If there are packages, then
    # 1) Get corresponding markup
    # markup = AM.choose_markup(1, len(packages))

    # 2) Add message text with N=5 packages on a page
    # In message show only address of package and its description
    # TODO: get message with packages func
    # msg = []
    # for i in range(min(5, len(packages))): # FIXME XXX AOAOOAOAO OMG MAGIC NUMBERS AOAOA XXX
    #     msg.append(
    #             f"{i+1}.\nОписание: {packages[i].description}"
    #     )
    # msg = "\n\n".join(msg)

    # When package is chosen, edit message text to show full info about
    # the package, and buttons [ Back ] [ Delete package ]
    # - will be done in callbacks

    await FSM.p_choose_package.set()

    async with state_proxy(dp) as storage:
        storage["packages"] = packages
        storage["current_page"] = 1
        storage["chosen_package_index"] = None

    await choose_package(call, dp.current_state())


async def choose_package(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        packages = storage["packages"]
        current_page = storage["current_page"]

        markup = AM.choose_markup(current_page, len(packages))
        msg = get_message_with_packages(current_page, packages)

        # 3) Edit current message to show packages and markup to choose them
        await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


async def next_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] += 1
    await choose_package(call, state)

async def prev_page(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        storage["current_page"] -= 1
    await choose_package(call, state)

async def choose_package_n(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as storage:
        match_ = re.findall(r"cb_choose(\d+)", call.data) # FIXME callback name hardcode aoaoaoao

        if match_ != []:
            n = int(match_[0])
            i = n - 1
            storage["chosen_package_index"] = i
        else:
            assert storage["chosen_package_index"] is not None
            i = storage["chosen_package_index"]

        package = storage["packages"][i]

    # 1) Get back_to_packages markup
    # 2) Create increment number of packages avaliable button
    # 3) Create delete package button
    markup = M.increase_decrease_delete_back()

    if package.amount <= 0:
        markup = M.increase_decrease_delete_back(False)

    msg = await get_message_with_full_package_info(i, package)

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
            )

async def back_to_packages(call: CallbackQuery, state: FSMContext):
    await choose_package(call, state)


async def delete_chosen_package(call: CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
            f"{call.message.text}\n\nВы действительно хотите удалить пакет?", # TODO -> MESSAGE of course
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.confirm_cancel_delete()
            )

async def confirm_delete(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state.proxy() as storage:
        i = storage["chosen_package_index"]
        package = storage["packages"][i]

    await db.delete_package(package.id)

    await call.answer("Пакет успешно удалён. ✅")

    await show_packages(call)

async def cancel_delete(call: CallbackQuery, state: FSMContext):
    await choose_package_n(call, state)

async def increment_amount(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state.proxy() as storage:
        i = storage["chosen_package_index"]
        package = storage["packages"][i]

        storage["packages"][i] = await db.get_by_id(Packages, package.id)

    await db.increment_package_amount(package.id)

    async with state.proxy() as storage:
        storage["packages"][i] = await db.get_by_id(Packages, package.id)

    msg = await get_message_with_full_package_info(i, package)

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.increase_decrease_delete_back()
            )

async def decrement_amount(call: CallbackQuery, state: FSMContext):
    db = await DBS.get_instance()

    async with state.proxy() as storage:
        i = storage["chosen_package_index"]
        package = storage["packages"][i]

    await db.decrement_package_amount(package.id)

    async with state.proxy() as storage:
        storage["packages"][i] = await db.get_by_id(Packages, package.id)

    msg = await get_message_with_full_package_info(i, package)

    down_arrow_fg = True if (package.amount - 1) > 0 else False

    await bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=M.increase_decrease_delete_back(down_arrow_fg)
            )

# Helpers
class M:
    """Markups class."""
    @staticmethod
    def increase_decrease_delete_back(decrease_arrow=True):
        markup = IKM(row_width=2)

        # TODO -> MESSAGE; callbacks aoaoaoa
        if decrease_arrow:
            markup.add(
                    IKB("⬆️ Количество", callback_data="cb_increase_amount"),
                    IKB("⬇️ Количество", callback_data="cb_decrease_amount")
                    )
        else:
            markup.add(
                    IKB("⬆️ Количество", callback_data="cb_increase_amount"),
                    )

        markup.add(
                IKB("🗑️ Удалить пакет", callback_data="cb_delete")
                )


        markup.add(
                IKB("Назад", callback_data="cb_back_to_packages")
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


def get_message_with_packages(page_number: int, packages: list[Packages.Record]) -> str:
    data = get_data_to_show_in_message(page_number, packages)

    message = []
    for d in data:
        message.append(MSG.FMT_PACKAGE.format(index=d["index"], package=d["record"]))

    message = "\n\n".join(message)

    return message

# TODO -> utils
async def get_full_package_info(package_: Packages.Record):
    db = await DBS.get_instance()

    # Needed to update changes in amount
    package = await db.get_by_id(Packages, package_.id)
    address = await db.get_by_id(Addresses, package.address_id)
    store = await db.get_by_id(Stores, address.store_id)

    result = {
            "store": store,
            "address": address,
            "package": package
            }

    return result

# TODO -> MESSAGE of course
async def get_message_with_full_package_info(index: int, package: Packages.Record):
    d = await get_full_package_info(package)

    msg = MSG.FMT_PACKAGE_FULL.format(
            index=index,
            store=d["store"],
            address=d["address"],
            package=d["package"]
            )

    msg = msg.split('\n')
    msg.pop(0)
    msg = "\n".join(msg)

    return "\n\n".join([f"Вы выбрали {index+1}.", msg])

from SnackSack.modules.partner.partner import FSM as pFSM

# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_packages"
    dp.register_callback_query_handler(show_packages, filter_, state=pFSM.p_default)#None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_prev_page"
    dp.register_callback_query_handler(prev_page, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_next_page"
    dp.register_callback_query_handler(next_page, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: re.match(r"cb_choose(\d+)", cb.data)
    dp.register_callback_query_handler(choose_package_n, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_back_to_packages"
    dp.register_callback_query_handler(back_to_packages, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_delete"
    dp.register_callback_query_handler(delete_chosen_package, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_cancel_delete"
    dp.register_callback_query_handler(cancel_delete, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_confirm_delete"
    dp.register_callback_query_handler(confirm_delete, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_increase_amount"
    dp.register_callback_query_handler(increment_amount, filter_, state=FSM.p_choose_package)

    filter_ = lambda cb: cb.data == "cb_decrease_amount"
    dp.register_callback_query_handler(decrement_amount, filter_, state=FSM.p_choose_package)
