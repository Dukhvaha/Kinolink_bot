from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import BASE_URL

FILMS_PER_PAGE = 8

def films_keyboard(films: list, page: int = 0) -> InlineKeyboardMarkup:
    total_pages = (len(films) - 1) // FILMS_PER_PAGE + 1
    start = page * FILMS_PER_PAGE
    end = start + FILMS_PER_PAGE
    page_films = films[start:end]

    buttons = []
    for film in page_films:
        name = film.get("name", "Без названия")
        year = film.get("year", "")
        film_id = film.get("id")
        media_type = film.get("media_type", "movie")
        icon = "📺" if media_type == "tv" else "🎬"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {name} ({year})",
                callback_data=f"movie_{media_type}_{film_id}"
            )
        ])

    # Навигация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"page_{page+1}"))

    if total_pages > 1:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def watch_keyboard(movie_id: int, media_type: str = "movie", imdb_id: str | None = None) -> InlineKeyboardMarkup:
    url = f'{BASE_URL}/?type={media_type}&id={movie_id}'
    telegram_callback = f"watch_tg_{media_type}_{imdb_id}" if imdb_id else "watch_tg_missing"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Открыть в Telegram",
                web_app=WebAppInfo(url=url)
            ),
            InlineKeyboardButton(
                text="🌐 Открыть в браузере",
                url=url
            )
        ],
        [
            InlineKeyboardButton(
                text="▶️ Смотреть в Telegram",
                callback_data=telegram_callback
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Назад к выбору",
                callback_data="back_to_results"
            )
        ]
    ])


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/KinoLink31")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")]
    ])


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Как смотреть фильмы", callback_data="help_movies"),
            InlineKeyboardButton(text="📺 Как смотреть сериалы", callback_data="help_series")
        ]
    ])
