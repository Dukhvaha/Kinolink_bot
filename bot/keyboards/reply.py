from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎬 Найти фильм")],
        [KeyboardButton(text="🔥 Популярное")],
        [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📢 Сотрудничество ")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="📊 Статистика")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def home_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Домой")],
        ],
        resize_keyboard=True
    )
