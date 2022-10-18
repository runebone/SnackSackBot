from aiogram.types import Message
from aiogram.dispatcher import FSMContext


class Error(Exception):
    """Base class for custom exceptions."""

    def __init__(self, message: Message, state: FSMContext | None = None):
        self.message = message
        self.state = state


class NoPackages(Error):
    pass

class PartnerNoPackages(Error):
    pass

class PartnerNoStores(Error):
    pass

class PartnerNoAddresses(Error):
    pass

class PartnerNoOrders(Error):
    pass
