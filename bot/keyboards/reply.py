from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Найти фильм")],
            [KeyboardButton(text="🔥 Популярное")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📢 По рекламе")],
        ],
        resize_keyboard=True
    )


def home_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Домой")],
        ],
        resize_keyboard=True
    )
