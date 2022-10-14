from aiogram import Dispatcher

from . import utils
from . import start
from . import client
from . import partner

def setup_handlers(dp: Dispatcher):
    partner.setup_handlers(dp)
    client.setup_handlers(dp)
    start.setup_handlers(dp)
