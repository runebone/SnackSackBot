from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack import DBS
from SnackSack.messages import MSG
from SnackSack.database.tables import Stores, Addresses, Orders, Packages

from .back_to_menu import cb_back_to_menu

async def get_addresses_list(chat_id: int):
    db = await DBS.get_instance()

    addresses = await db.get_partner_addresses(chat_id)

    return addresses

async def get_stores_list(chat_id: int):
    db = await DBS.get_instance()

    addresses = await get_addresses_list(chat_id)

    stores = []
    stores_names = []
    for address in addresses:
        # FIXME: extra work, not very effective
        store = await db.get_by_id(Stores, address.store_id)

        if store.name not in stores_names:
            stores_names.append(store.name)
            stores.append(store)

    return stores

class M:
    """Markups class."""
    @staticmethod
    def stores(stores_names: list[str], cb_choose_store: str):
        markup = IKM(row_width=1)

        i = 0
        for store_name in stores_names:
            markup.add(
                IKB(f"{store_name}", callback_data=f"{cb_choose_store}{i}")
            )
            i += 1

        markup.add(IKB(MSG.BTN_BACK, callback_data=cb_back_to_menu)) # FIXME UGLY

        return markup
