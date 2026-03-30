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
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {name} ({year})",
                callback_data=f"movie_{film_id}"
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

def watch_keyboard(movie_id:int) -> InlineKeyboardMarkup:
    url = f'{BASE_URL}/?id={movie_id}'
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📱 Смотреть в Telegram",
            web_app=WebAppInfo(url=url)
        ),
        InlineKeyboardButton(
            text="🌐 В браузере",
            url=url
        )
    ]])
