from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Найти фильм")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📢 По рекламе")],
        ],
        resize_keyboard=True
    )