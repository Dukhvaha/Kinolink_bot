import httpx
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/movies/{movie_id}")

    if response.status_code != 200:
        await callback.answer("Ошибка загрузки фильма", show_alert=True)
        return

    movie = response.json()

    name = movie.get("name", "Без названия")
    year = movie.get("year", "")
    poster = movie.get("poster")

    caption = (
        f"🎬 *{name}* ({year})\n"
    )

    await callback.message.answer_photo(
        photo=poster,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=watch_keyboard(movie_id)
    )
    await callback.answer()