from aiogram import Dispatcher

def state_proxy(dp: Dispatcher):
    return dp.current_state().proxy()
