from SnackSack import dp, db, bot
from SnackSack.messages import MSG

from SnackSack.database.package import Package

from aiogram import types

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

import re


class FSM(StatesGroup):
    choose_package = State()


@dp.message_handler(text=MSG.CLIENT_BTN, state=None)
async def client(message: types.Message):

    msg, markup = get_records_message_and_markup(0)

    package_records = get_package_records()
    if len(package_records) > 5:
        markup.add(
                IKB("Назад", callback_data="cb_back"),
                IKB("->", callback_data="cb_next_page")
                )
    else:
        # FIXME: ugly, DRY
        markup.add(
                IKB("Назад", callback_data="cb_back"),
                )

    packages_list_message = await message.answer(msg, reply_markup=markup)
    await FSM.choose_package.set()

    async with dp.current_state().proxy() as data:
        data["current_page"] = 1
        data["chosen_package_index"] = None
        data["packages_list_message"] = packages_list_message
        data["message_id"] = None


@dp.callback_query_handler(lambda cb: cb.data == "cb_next_page", state=FSM.choose_package)
async def handle_callback_next_page(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        msg, markup = get_records_message_and_markup(data["current_page"] * 5) # FIXME: magic numbers
        if len(get_package_records()) > data["current_page"] * 5 + 5: # FIXME: very very ugly
            markup.add(
                    IKB("<-", callback_data="cb_prev_page"),
                    IKB("Назад", callback_data="cb_back"),
                    IKB("->", callback_data="cb_next_page")
                    )
        else:
            # FIXME: ugly, DRY
            markup.add(
                    IKB("<-", callback_data="cb_prev_page"),
                    IKB("Назад", callback_data="cb_back")
                    )

        await bot.edit_message_text(
                msg,
                call.message.chat.id,
                data["packages_list_message"].message_id,
                reply_markup=markup
                )

        data["current_page"] += 1


@dp.callback_query_handler(lambda cb: cb.data == "cb_prev_page", state=FSM.choose_package)
async def handle_callback_prev_page(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data["current_page"] -= 1
        msg, markup = get_records_message_and_markup(data["current_page"] * 5 - 5) # FIXME: magic numbers
        if data["current_page"] == 1:
            markup.add(
                IKB("Назад", callback_data="cb_back"),
                IKB("->", callback_data="cb_next_page")
                )
        else:
            markup.add(
                    IKB("<-", callback_data="cb_prev_page"),
                    IKB("Назад", callback_data="cb_back"),
                    IKB("->", callback_data="cb_next_page")
                    )

        await bot.edit_message_text(
                msg,
                call.message.chat.id,
                data["packages_list_message"].message_id,
                reply_markup=markup
                )


def get_package_records():
    return db["package"].records


def get_records_message_and_markup(start_index: int = 0):
    i = start_index
    msg = []
    package_records = get_package_records()
    for record in package_records[start_index:start_index+5]:
        msg.append(f"{i+1}. {Package.from_json(record)}")
        i += 1

    markup = IKM(row_width=5)

    buttons = []
    for j in range(start_index, i):
        buttons.append(IKB(f"{j+1}", callback_data=f"cb{j+1}"))
    markup.add(*buttons)

    return ("\n\n".join(msg), markup)


@dp.callback_query_handler(lambda cb: re.match(r"cb(\d+)", cb.data), state=FSM.choose_package)
async def handle_callback_n(call: types.CallbackQuery, state: FSMContext):
    markup = IKM(row_width=2)
    markup.add(
            IKB("✅ Подтвердить", callback_data="cb_confirm"),
            IKB("🚫 Отмена", callback_data="cb_cancel")
            )

    async with state.proxy() as data:
        n = int(re.findall(r"cb(\d+)", call.data)[0])

        record_text = Package.from_json(db["package"].records[n - 1])

        if data["message_id"] == None:
            msg = await bot.send_message(call.message.chat.id,
                    f"<b>Вы выбрали:</b>\n{record_text}",
                    reply_markup=markup
                    )
            data["message_id"] = msg.message_id
            data["chosen_package_index"] = n - 1
        else:
            msg = await bot.edit_message_text(
                    f"<b>Вы выбрали:</b>\n{record_text}",
                    call.message.chat.id,
                    data["message_id"],
                    reply_markup=markup
                    )
            data["chosen_package_index"] = n - 1

    # await state.finish()


@dp.callback_query_handler(lambda cb: cb.data == "cb_back", state=FSM.choose_package)
async def handle_callback_back(call: types.CallbackQuery, state: FSMContext):
    await call.answer("ℹ️ Вы вышли из режима выбора пакета.")
    # from SnackSack.handlers.start import keyboard
    await bot.edit_message_text(
            MSG.DEFAULT,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
            )
    await state.finish()


@dp.callback_query_handler(lambda cb: cb.data == "cb_cancel", state=FSM.choose_package)
async def handle_callback_cancel(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await bot.edit_message_text(
                f"🚫 {call.message.text}",
                call.message.chat.id,
                data["message_id"],
                reply_markup=None
                )
    await state.finish()


@dp.callback_query_handler(lambda cb: cb.data == "cb_confirm", state=FSM.choose_package)
async def handle_callback_confirm(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await bot.edit_message_text(
                f"✅ {call.message.text}",
                call.message.chat.id,
                data["message_id"],
                reply_markup=None
                )
    # TODO: send invoice and shipping info etc; checkout from db after
    # successful payment
    await state.finish()
