from aiogram import Dispatcher

from . import utils
from . import start
from . import client
from . import partner

from . import stores

def setup_handlers(dp: Dispatcher):
    stores.setup_handlers(dp)
    partner.setup_handlers(dp)
    client.setup_handlers(dp)
    start.setup_handlers(dp)
