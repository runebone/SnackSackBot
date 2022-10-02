from SnackSack import dp
from SnackSack.messages import MSG

from aiogram import types

from aiogram.types.reply_keyboard import KeyboardButton as KB
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup as RKB

client_button = KB(text=MSG.CLIENT_BTN)
partner_button = KB(text=MSG.PARTNER_BTN)

keyboard = RKB(resize_keyboard=True, one_time_keyboard=True)
keyboard = keyboard.row(client_button, partner_button)

@dp.message_handler(commands=["start"], state="*")
async def start(message: types.Message):
    await message.answer(MSG.START, reply_markup=keyboard)
