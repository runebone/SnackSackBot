class RU:
    START = """🌟 Здравствуйте! Я бот <b>SnackSack</b> ✨
Для того, чтобы начать, выберите, кто вы:"""
    DEFAULT = "Для продолжения выберите, кто вы:"

    BTN_CLIENT = "Я клиент"
    BTN_PARTNER = "Я партнёр"

    BTN_BACK = "Назад"
    BTN_ARROW_FORWARD = "->"
    BTN_ARROW_BACK = "<-"

    FMT_PACKAGE = "{index}.\n\
Описание: {package.description}\n\
Цена одного пакета: {package.price}\n\
Забрать до: {package.time}\n\
Осталось пакетов: {package.amount}\
"

    FMT_ORDER_HEADER = "Заказ `{order_number}`:"
    FMT_ORDER_BODY = "\
Описание: {description}\n\
Цена: {price}\
            "

    FMT_PACKAGE_FULL = "{index}.\n\
Магазин: {store.name}\n\
Адрес: {address.address}\n\
Описание: {package.description}\n\
Цена одного пакета: {package.price}\n\
Забрать до: {package.time}\n\
Осталось пакетов: {package.amount}\
"

    FMT_ADDRESS = "{index}. {address.address}"

    FMT_YOU_HAVE_CHOSEN = "<b>Вы выбрали: {index}</b>\n\
Описание: {package.description}\n\
Забрать до: {package.time}\n\
Осталось пакетов: {package.amount}\
" # FIXME: DRY

    EXITED_CHOOSE_PACKAGE_MODE = "ℹ️ Вы вышли из режима выбора пакета."

    BTN_CONFIRM = "✅ Подтвердить"
    BTN_CANCEL = "❌ Отмена"

    FMT_DEMO_INITIAL_PARNTER_MENU = "Добро пожаловать, {username}! ✨"

    NO_PACKAGES_YET = "У вас пока нет пакетов. 📭"
    NO_STORES_YET = "У вас пока нет магазинов. 🏡"
    NO_ORDERS_YET = "У вас пока нет заказов. 🧾"


MSG = RU
