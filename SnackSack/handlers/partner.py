from SnackSack import dp, db, bot
from SnackSack.messages import MSG

from SnackSack.database.partner import Partner

from aiogram import types

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

import re


class FSM(StatesGroup):
    create_partner = State()

    create_package = State()
    input_description = State()
    input_time = State()
    input_number_of_packages = State()
    input_price = State()
    final = State()


@dp.message_handler(text=MSG.PARTNER_BTN, state=None)
async def partner(message: types.Message):
    # 1) Get partner database
    partners_records = map(Partner.from_json, db["partner"].records)

    # 2) Lookup for chat_id in partner database
    partners_chat_ids = [record.chat_id for record in partners_records]

    # 3) If chat_id is not found, ask partner to input his shop name and add
    # new partner to database (tell him that it will be shown to clients)
    if message.chat.id not in partners_chat_ids:
        # XXX meh ugly
        markup = IKM(row_width=2)
        yes_btn = IKB("Да", callback_data="cb_yes")
        no_btn = IKB("Нет", callback_data="cb_no")
        markup.add(yes_btn, no_btn)

        await message.answer(
            "Упс, похоже, вас нет в базе данных. Хотите стать партнёром?",
            reply_markup=markup,
        )
    else:
        markup = get_partner_menu_markup()
        await message.answer(
            f"Добро пожаловать, <b>{message.from_user.first_name}</b>! ✨",
            reply_markup=markup,
        )


@dp.callback_query_handler(lambda cb: cb.data == "cb_yes", state=None)
async def handle_callback_create_partner(call: types.CallbackQuery):
    await FSM.create_partner.set()
    await call.answer("✅")  # TODO: all messages -> message
    await bot.edit_message_text(
        call.message.text + " ✅",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )
    await bot.send_message(call.message.chat.id, "Введите название своего магазина:")


@dp.callback_query_handler(lambda cb: cb.data == "cb_no", state=None)
async def handle_callback_dont_create_partner(call: types.CallbackQuery):
    await call.answer("🚫")
    await bot.edit_message_text(
        call.message.text + " 🚫",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )


@dp.message_handler(state=FSM.create_partner)
async def create_partner(message: types.Message, state: FSMContext):
    # XXX ugly; refactor
    partners_records = db["partner"].records
    DEMO_RECORD_INDEX = 0
    demo_record = Partner.from_json(partners_records[DEMO_RECORD_INDEX])
    demo_record.change_uuid()
    demo_record.chat_id = message.chat.id
    db["partner"].create(demo_record)
    db["partner"].update_file()
    await state.finish()
    await message.answer("✅ Вы успешно зарегистрированы в качестве партнёра.")


def get_partner_menu_markup():
    markup = IKM(row_width=1)

    my_shops_btn = IKB("Мои магазины", callback_data="cb_my_shops")
    my_orders_btn = IKB("Мои заказы", callback_data="cb_my_orders")
    my_packages_btn = IKB("Мои пакеты", callback_data="cb_my_packages")
    create_package_btn = IKB("Создать пакет", callback_data="cb_create_package")

    markup.add(my_shops_btn, my_orders_btn, my_packages_btn, create_package_btn)

    return markup


def get_partner(chat_id: int) -> Partner | None:
    partner = None
    for record in db["partner"].records:
        if record["chat_id"] == chat_id:
            partner = record
            break  # FIXME

    if partner != None:
        partner = Partner.from_json(partner)

    return partner


def get_shops_menu_markup(chat_id: int):
    partner = get_partner(chat_id)
    assert partner != None, "ERROR: partner not found"

    shops = partner.stores

    markup = IKM(row_width=1)

    buttons = [IKB(shops[i], callback_data=f"cb_shop{i}") for i in range(len(shops))]
    back_btn = IKB("Назад", callback_data="cb_back_to_partner_menu")

    markup.add(*buttons, back_btn)

    return markup


@dp.callback_query_handler(lambda cb: cb.data == "cb_my_shops", state="*")
async def handle_callback_my_shops(call: types.CallbackQuery, state: FSMContext):
    if state != None:
        await state.finish()

    markup = get_shops_menu_markup(call.message.chat.id)

    await bot.edit_message_text(
        "🏡 Ваши магазины:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


def get_random_nature_emoji():
    from numpy.random import choice

    nature_emojis = "🍀🍁🌺🌲🌳🌻🍂"
    return choice(list(nature_emojis))


@dp.callback_query_handler(lambda cb: cb.data == "cb_back_to_partner_menu", state="*")
async def handle_callback_back_to_partner_menu(
    call: types.CallbackQuery, state: FSMContext
):
    if state != None:
        await state.finish()

    await bot.edit_message_text(
        f"{get_random_nature_emoji()} Меню {get_random_nature_emoji()}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_partner_menu_markup(),
    )


@dp.callback_query_handler(lambda cb: re.match(r"cb_shop(\d+)", cb.data), state=None)
async def handle_callback_shop_n(call: types.CallbackQuery):
    shop_index = int(re.findall(r"cb_shop(\d+)", call.data)[0])

    partner = get_partner(call.message.chat.id)
    assert partner != None, "ERROR: partner not found"

    shop_name = partner.stores[shop_index]

    addresses = []
    for address in partner.addresses:
        if address["store"] == shop_name:
            addresses.append(address["address"])

    msg = [f"{i+1}. {addresses[i]}" for i in range(len(addresses))]
    msg = f"🏤 Адреса <b>{shop_name}</b>:\n\n" + "\n".join(msg)

    markup = IKM(row_width=1)

    add_new_address = IKB(
        "Добавить новый адрес", callback_data="cb_unavaliable_in_demo"
    )
    change_address = IKB("Изменить адрес", callback_data="cb_unavaliable_in_demo")
    delete_address = IKB("Удалить адрес", callback_data="cb_unavaliable_in_demo")

    markup.add(add_new_address, change_address, delete_address)

    markup.add(IKB("Назад", callback_data="cb_my_shops"))

    await bot.edit_message_text(
        msg, call.message.chat.id, call.message.message_id, reply_markup=markup
    )


@dp.callback_query_handler(lambda cb: cb.data == "cb_my_orders", state=None)
async def handle_callback_my_orders(call: types.CallbackQuery):
    partner = get_partner(call.message.chat.id)
    assert partner != None, "ERROR: partner not found"

    orders = partner.orders

    if orders == []:
        await bot.send_message(call.message.chat.id, "ℹ️ У вас нет текущих заказов.")
    else:
        # TODO
        pass


@dp.callback_query_handler(lambda cb: cb.data == "cb_my_packages", state=None)
async def handle_callback_my_packages(call: types.CallbackQuery):
    partner = get_partner(call.message.chat.id)
    assert partner != None, "ERROR: partner not found"

    packages = partner.packages

    if packages == []:
        markup = IKM(row_width=1)
        create_package_btn = IKB("Создать пакет", callback_data="cb_create_package")
        markup.add(create_package_btn)

        await bot.send_message(
            call.message.chat.id,
            "ℹ️ У вас пока нет пакетов, но вы можете создать их:",
            reply_markup=markup,
        )
    else:
        msg = [f"{i+1}. {packages[i]}\n/delete{i+1}" for i in range(len(packages))]
        msg = "📦 <b>Ваши пакеты:</b>\n\n" + "\n\n".join(msg)
        msg = (
            msg
            + "\n\n<i>Вне демо-версии, вместо UUID должна будет подцепляться информация о пакете из БД пакетов.</i>"
        )

        markup = IKM(row_width=1)
        markup.add(IKB("Назад", callback_data="cb_back_to_partner_menu"))

        await bot.edit_message_text(
            msg, call.message.chat.id, call.message.message_id, reply_markup=markup
        )


# FIXME XXX
from aiogram.dispatcher import filters


@dp.message_handler(
    filters.RegexpCommandsFilter(regexp_commands=["/delete([0-9]*)"]), state=None
)
async def delete_package(message: types.Message):
    await message.answer("ℹ️ Команда недоступна в демо-версии.")


@dp.callback_query_handler(lambda cb: cb.data == "cb_create_package", state=None)
async def handle_callback_create_package(call: types.CallbackQuery):
    await FSM.create_package.set()

    async with dp.current_state().proxy() as data:
        data["shop_index"] = None
        data["shop_name"] = None
        data["address"] = None
        data["description"] = None
        data["time"] = None
        data["number_of_packages"] = None
        data["price"] = None

    # FIXME: DRY
    partner = get_partner(call.message.chat.id)
    assert partner != None, "ERROR: partner not found"

    shops = partner.stores

    markup = IKM(row_width=1)

    buttons = [
        IKB(shops[i], callback_data=f"cb_choose_shop{i}") for i in range(len(shops))
    ]
    back_btn = IKB("Назад", callback_data="cb_back_to_partner_menu")

    markup.add(*buttons, back_btn)

    await bot.edit_message_text(
        "Выберите магазин:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


@dp.callback_query_handler(
    lambda cb: re.match(r"cb_choose_shop(\d+)", cb.data), state=FSM.create_package
)
async def handle_callback_choose_shop_n(call: types.CallbackQuery, state: FSMContext):
    # FIXME: ugly
    async with state.proxy() as data:
        shop_index = int(re.findall(r"cb_choose_shop(\d+)", call.data)[0])

        partner = get_partner(call.message.chat.id)
        assert partner != None, "ERROR: partner not found"

        shop_name = partner.stores[shop_index]

        data["shop_index"] = shop_index
        data["shop_name"] = shop_name

        addresses = []
        for address in partner.addresses:
            if address["store"] == shop_name:
                addresses.append(address["address"])

        msg = [f"{i+1}. {addresses[i]}" for i in range(len(addresses))]
        msg = f"Выберите адрес <b>{shop_name}</b>:\n\n" + "\n".join(msg)

        markup = IKM(row_width=len(addresses))  # FIXME XXX: change pages; 5

        buttons = [
            IKB(f"{i+1}", callback_data=f"cb_choose_address{i}")
            for i in range(len(addresses))
        ]

        markup.add(*buttons)
        markup.add(IKB("Назад", callback_data="cb_my_shops"))

        await bot.edit_message_text(
            msg, call.message.chat.id, call.message.message_id, reply_markup=markup
        )


@dp.callback_query_handler(
    lambda cb: re.match(r"cb_choose_address(\d+)", cb.data), state=FSM.create_package
)
async def handle_callback_choose_address_n(
    call: types.CallbackQuery, state: FSMContext
):
    async with state.proxy() as data:
        address_index = int(re.findall(r"cb_choose_address(\d+)", call.data)[0])

        partner = get_partner(call.message.chat.id)
        assert partner != None, "ERROR: partner not found"

        address = partner.addresses[address_index]["address"]

        data["address"] = address

        await bot.edit_message_text(
            "Введите описание пакета:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None,
        )

        # ??? will it share data with the previous state ??? FIXME
        await FSM.input_description.set()


@dp.message_handler(state=FSM.input_description)
async def input_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text

    await bot.send_message(
        message.chat.id, "Введите время, до которого нужно забрать пакет:"
    )
    await FSM.input_time.set()


@dp.message_handler(state=FSM.input_time)
async def input_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["time"] = message.text

    await bot.send_message(message.chat.id, "Введите количество пакетов:")
    await FSM.input_number_of_packages.set()


@dp.message_handler(state=FSM.input_number_of_packages)
async def input_number_of_packages(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["number_of_packages"] = message.text

    await bot.send_message(message.chat.id, "Введите цену одного пакета:")
    await FSM.input_price.set()


@dp.message_handler(state=FSM.input_price)
async def input_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["price"] = int(message.text)  # FIXME error handle of course everywhere

        # FIXME: DRY; copied from __str__ of package
        msg = f"""<b>Магазин</b>: {data["shop_name"]}
<b>Адрес</b>:\n{data["address"]}
<b>Описание</b>:\n{data["description"]}
<b>Забрать до</b>: {data["time"]}
<b>Кол-во</b>: {data["number_of_packages"]}
<b>Цена (за 1 шт.)</b>: {data["price"]}"""

    msg = "<b>Итого:</b>\n\n" + msg

    markup = IKM(row_width=2)
    markup.add(
        IKB("✅ Подтвердить", callback_data="cb_confirm"),
        IKB("🚫 Отмена", callback_data="cb_cancel"),
    )

    await bot.send_message(message.chat.id, msg, reply_markup=markup)
    await FSM.final.set()


@dp.callback_query_handler(lambda cb: cb.data == "cb_confirm", state=FSM.final)
async def handle_callback_confirm(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
        "✅ " + call.message.text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )

    from SnackSack.database.package import Package

    async with state.proxy() as data:
        created_package = Package(
            data["shop_name"],
            data["address"],
            data["description"],
            data["time"],
            data["number_of_packages"],
            data["price"],
        )

        db["package"].records.append(created_package.to_json())
        db["package"].update_file()

    await state.finish()


@dp.callback_query_handler(lambda cb: cb.data == "cb_cancel", state=FSM.final)
async def handle_callback_cancel(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
        "🚫 " + call.message.text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None,
    )
    await state.finish()
    # TODO: show menu or something


@dp.callback_query_handler(lambda cb: cb.data == "cb_unavaliable_in_demo", state=None)
async def handle_callback_unavaliable_in_demo(call: types.CallbackQuery):
    await call.answer("Недоступно в демо-версии.", show_alert=True)
