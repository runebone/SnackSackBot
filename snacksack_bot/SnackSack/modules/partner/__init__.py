from aiogram import Dispatcher

from . import partner
from . import stores
from . import addresses
from . import packages
from . import create_package

from . import back_to_menu

def setup_handlers(dp: Dispatcher):
    partner.setup_handlers(dp)
    packages.setup_handlers(dp)
    back_to_menu.setup_handlers(dp)
    stores.setup_handlers(dp)
    ...
