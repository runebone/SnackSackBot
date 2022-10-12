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
    markup = AM.choose_markup(1, len(packages))

    # 2) Add message text with N=5 packages on a page
    # In message show only address of package and its description
    msg = []
    for i in range(min(5, len(packages))): # FIXME XXX AOAOOAOAO OMG MAGIC NUMBERS AOAOA XXX
        msg.append(
                f"{i+1}.\nОписание: {packages[i].description}"
        )
    msg = "\n\n".join(msg)

    # 3) Edit current message to show packages and markup to choose them
    await bot.edit_message_text(
        msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

    # When package is chosen, edit message text to show full info about
    # the package, and buttons [ Back ] [ Delete package ]
    # - will be done in callbacks

    await FSM.p_choose_package.set()

    async with state_proxy(dp) as storage:
        storage["packages"] = packages
        storage["current_page"] = 1
        storage["chosen_package_index"] = None

# Helpers
class M:
    """Markups class."""
    pass


# Setup handlers
def setup_handlers(dp: Dispatcher):
    filter_ = lambda cb: cb.data == "cb_my_packages"
    dp.register_callback_query_handler(show_packages, filter_, state=None)

    register_back_to_menu_handler_from_new_state(dp, FSM.p_choose_package)
