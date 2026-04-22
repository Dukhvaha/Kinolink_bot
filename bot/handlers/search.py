import httpx
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import BASE_URL
from bot.keyboards.inline import films_keyboard, watch_keyboard
from bot.handlers.start import is_subscribed
from config import CHANNEL_BOT_ID, BACKEND_URL

router = Router()

class SearchState(StatesGroup):
    waiting_for_query = State()


@router.message(F.text == "🎬 Найти фильм")
async def handle_search_button(message: Message, state: FSMContext, bot: Bot):
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("❌ Для использования бота подпишитесь на канал!")
        return

    await state.set_state(SearchState.waiting_for_query)
    await message.answer("🔍 Введите название фильма или сериала:")


@router.message(SearchState.waiting_for_query)
async def handle_query(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()

    searching_msg = await message.answer("⏳ Ищу...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/search",
            params={"query": query}
        )

    await searching_msg.delete()

    if response.status_code != 200 or not response.json():
        await message.answer("😔 Ничего не найдено, попробуй другой запрос.")
        return

    films = response.json()

    # Сохраняем результаты в state
    await state.set_data({"films": films})

    await message.answer(
        f"🎬 Результаты по запросу *{query}*:",
        parse_mode="Markdown",
        reply_markup=films_keyboard(films, page=0)
    )


@router.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    films = data.get("films", [])

    if not films:
        await callback.answer("Сделай новый поиск")
        return

    await callback.message.edit_reply_markup(
        reply_markup=films_keyboard(films, page=page)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("movie_"))
async def handle_movie_select(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/movies/{movie_id}")
    except httpx.TimeoutException:
        await callback.answer("⏱ Сервер не отвечает, попробуй позже.", show_alert=True)
        return
    except Exception:
        await callback.answer("❌ Что-то пошло не так.", show_alert=True)
        return

    if response.status_code != 200:
        await callback.answer("Ошибка загрузки фильма", show_alert=True)
        return

    movie = response.json()
    name = movie.get("name", "Без названия")
    year = movie.get("year", "")
    rating = movie.get("rating", 0)
    poster = movie.get("poster")

    caption = (
        f"🎬 *{name}* ({year})\n"
        f"⭐️ {rating}"
    )

    await callback.message.answer_photo(
        photo=poster,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=watch_keyboard(movie_id)
    )
    await callback.answer()

@router.message(F.text == "🔥 Популярное")
async def handle_novelties(message: Message, state: FSMContext, bot: Bot):
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("❌ Для использования бота подпишитесь на канал!")
        return

    msg = await message.answer("⏳ Загружаю новинки...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/novelties")
        films = response.json() if response.status_code == 200 else []
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка загрузки новинок.")
        return

    await msg.delete()

    if not films:
        await message.answer("😔 Новинки не найдены.")
        return

    # Берём только 6 фильмов
    films = films[:6]
    await state.set_data({"films": films})

    await message.answer(
        "🔥 *Новинки — выбери фильм:*",
        parse_mode="Markdown",
        reply_markup=films_keyboard(films, page=0)
    )

@router.message(F.text == "🎲 Случайный фильм")
async def handle_random(message: Message, bot: Bot):
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("❌ Для использования бота подпишитесь на канал!")
        return
    await show_random_film(message, bot)


@router.callback_query(F.data == "random_next")
async def handle_random_next(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    await show_random_film(callback.message, bot)
    await callback.answer()


async def show_random_film(message: Message, bot: Bot):
    msg = await message.answer("🎲 Ищу случайный фильм...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/random")
        film = response.json() if response.status_code == 200 else None
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка.")
        return

    await msg.delete()

    if not film:
        await message.answer("😔 Не удалось найти фильм.")
        return

    movie_id = film.get("id")

    # Получаем полные данные фильма
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            full = await client.get(f"{BACKEND_URL}/movies/{movie_id}")
        movie = full.json() if full.status_code == 200 else {}
    except Exception:
        movie = {}

    name = movie.get("name") or film.get("name", "Без названия")
    year = movie.get("year") or film.get("year", "")
    rating = movie.get("rating", 0)
    description = movie.get("description", "Описание отсутствует.")
    poster = movie.get("poster") or film.get("poster")

    caption = (
        f"🎲 *Случайный фильм*\n\n"
        f"🎬 *{name}* ({year})\n"
        f"⭐️ {rating}\n\n"
        f"{description[:500]}{'...' if len(description) > 500 else ''}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Смотреть в Telegram", web_app=WebAppInfo(url=f"{BASE_URL}/?id={movie_id}")),
            InlineKeyboardButton(text="🌐 В браузере", url=f"{BASE_URL}/?id={movie_id}")
        ],
        [InlineKeyboardButton(text="🎲 Другой фильм", callback_data="random_next")]
    ])

    await message.answer_photo(
        photo=poster,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=keyboard
    )