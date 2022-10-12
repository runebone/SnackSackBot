from aiogram import Dispatcher
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM

from SnackSack.messages import MSG

MAX_NUMBER_OF_ELEMENTS_ON_A_PAGE = 5
N = 5

def state_proxy(dp: Dispatcher):
    return dp.current_state().proxy()

class M:
    """Common markups class."""

    @staticmethod
    def partner_menu():
        markup = IKM(row_width=1)

        # TODO move to MESSAGE
        my_shops_btn = IKB("Мои магазины 🏡", callback_data="cb_my_shops")
        my_orders_btn = IKB("Мои заказы 🧾", callback_data="cb_my_orders")
        my_packages_btn = IKB("Мои пакеты 🛍️", callback_data="cb_my_packages")
        create_package_btn = IKB("Создать пакет 🆕📦", callback_data="cb_create_package")

        markup.add(my_shops_btn, my_orders_btn, my_packages_btn, create_package_btn)

        return markup

class ArrowsMarkup:
    def __init__(self, cb_back: str, cb_arrow_back: str, cb_arrow_forward: str, cb_choose: str, row_width: int = N):
        self.cb_back = cb_back
        self.cb_arrow_back = cb_arrow_back
        self.cb_arrow_forward = cb_arrow_forward
        self.fmt_cb_choose_index = "".join([cb_choose, "{index}"])
        self.row_width = row_width

    def _get_number_buttons_markup(self, page_number: int, number_of_elements_on_a_page: int, max_number_of_elements_on_a_page: int = N):
        markup = IKM(row_width=self.row_width)

        start_index = (page_number - 1) * max_number_of_elements_on_a_page

        buttons = []
        for i in range(start_index, start_index + number_of_elements_on_a_page):
            buttons.append(
                IKB(f"{i+1}", callback_data=self.fmt_cb_choose_index.format(index=i+1))
            )
        markup.add(*buttons)

        return markup

    def back_button(self, page_number: int, number_of_elements_on_a_page: int, max_number_of_elements_on_a_page: int = N):
        markup = self._get_number_buttons_markup(page_number, number_of_elements_on_a_page, max_number_of_elements_on_a_page)

        markup.add(
            IKB(MSG.BTN_BACK, callback_data=self.cb_back),
        )

        return markup

    def back_button_and_arrow_forward(self, page_number: int, number_of_elements_on_a_page: int, max_number_of_elements_on_a_page: int = N):
        markup = self._get_number_buttons_markup(page_number, number_of_elements_on_a_page, max_number_of_elements_on_a_page)

        markup.add(
            IKB(MSG.BTN_BACK, callback_data=self.cb_back),
            IKB(MSG.BTN_ARROW_FORWARD, callback_data=self.cb_arrow_forward),
        )

        return markup

    def both_arrows_and_back_button(self, page_number: int, number_of_elements_on_a_page: int, max_number_of_elements_on_a_page: int = N):
        markup = self._get_number_buttons_markup(page_number, number_of_elements_on_a_page, max_number_of_elements_on_a_page)

        markup.add(
            IKB(MSG.BTN_ARROW_BACK, callback_data=self.cb_arrow_back),
            IKB(MSG.BTN_BACK, callback_data=self.cb_back),
            IKB(MSG.BTN_ARROW_FORWARD, callback_data=self.cb_arrow_forward),
        )

        return markup

    def arrow_back_and_back_button(self, page_number: int, number_of_elements_on_a_page: int, max_number_of_elements_on_a_page: int = N):
        markup = self._get_number_buttons_markup(page_number, number_of_elements_on_a_page, max_number_of_elements_on_a_page)

        markup.add(
            IKB(MSG.BTN_ARROW_BACK, callback_data=self.cb_arrow_back),
            IKB(MSG.BTN_BACK, callback_data=self.cb_back),
        )

        return markup

    def choose_markup(self, page_number: int, total_number_of_elements: int, max_number_of_elements_on_a_page: int = N) -> IKM:
        assert page_number > 0, "Invalid page number."
        assert total_number_of_elements >= 0, "Invalid number of elements."

        N = max_number_of_elements_on_a_page

        # n - number of elements on a page
        n = min(N, total_number_of_elements - N * (page_number - 1))

        if page_number == 1:
            if N < total_number_of_elements:
                return self.back_button_and_arrow_forward(
                    page_number,
                    n,
                    max_number_of_elements_on_a_page
                )
            return self.back_button(
                page_number,
                n,
                max_number_of_elements_on_a_page
            )

        # page_number > 1
        if page_number * N < total_number_of_elements:
            return self.both_arrows_and_back_button(
                page_number,
                n,
                max_number_of_elements_on_a_page
            )
        return self.arrow_back_and_back_button(
            page_number,
            n,
            max_number_of_elements_on_a_page
        )
