from SnackSack import dp, db, bot
from SnackSack.messages import MSG

from aiogram import types

from SnackSack.config import PAYMENT_TOKEN
from aiogram.types import ShippingOption, ShippingQuery, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType


class Product:
    def __init__(self, title: str, description: str, label: str, price: int):
        self.title = title
        self.description = description
        self.currency = "rub"
        self.prices = [
                LabeledPrice(label=label, amount=(price * 100))
                ]


async def buy(message: types.Message, product: Product):
    await bot.send_invoice(message.chat.id,
            title=product.title,
            description=product.description,
            provider_token=PAYMENT_TOKEN,
            currency=product.currency,
            prices=product.prices,
            payload="buy_payload_idk",
            photo_url="https://i.pinimg.com/736x/6a/d4/a8/6ad4a89ea2c98ca7fc2285f66cc1c970.jpg",
            photo_width=640,
            photo_height=640,
            photo_size=640,
            is_flexible=True,
            start_parameter="example_aoaoa",
            need_shipping_address=False
            )


@dp.shipping_query_handler(lambda q: True)
async def shipping_process(shipping_query: ShippingQuery):
    if shipping_query.shipping_address.country_code != "RU":
        return await bot.answer_shipping_query(
                shipping_query.id,
                ok=False,
                error_message="Россию там выбрать надо да."
                )

    pickup = ShippingOption(
            id="pickup",
            title="Самовывоз"
            )
    pickup.add(LabeledPrice("Самовывоз в Москве", 0))

    shipping_options = [ pickup ]

    await bot.answer_shipping_query(
            shipping_query.id,
            ok=True,
            shipping_options=shipping_options
            )


@dp.pre_checkout_query_handler(lambda q: True)
async def checkout_process(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    await bot.send_message(
            message.chat.id,
            f"Успешная оплата ({message.successful_payment.total_amount // 100} руб.) ✅"
            )
