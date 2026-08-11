from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from config import BASE_URL


def movie_roulette_url() -> str:
    return f"{(BASE_URL or 'http://127.0.0.1:8000').rstrip('/')}/apps/movie-roulette"


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎬 Найти фильм")],
        [KeyboardButton(text="🔥 Популярное")],
        [KeyboardButton(text="🎲 Movie Roulette", web_app=WebAppInfo(url=movie_roulette_url()))],
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
