from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.inline import films_keyboard
from bot.keyboards.reply import home_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.movie_service import search_movies
from bot.services.statistics import log_event, track_user
from bot.services.subscription import is_subscribed

router = Router()

class SearchState(StatesGroup):
    waiting_for_query = State()


@router.message(F.text == "🎬 Найти фильм")
async def handle_search_button(message: Message, state: FSMContext, bot: Bot):
    track_user(message.from_user)
    log_event(message.from_user.id, "search_button")

    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("❌ Для использования бота подпишитесь на канал!")
        return

    await clear_last_results_keyboard(bot, state, message.chat.id)
    await state.set_state(SearchState.waiting_for_query)
    await message.answer(
        "🔍 Введите название фильма или сериала:",
        parse_mode="Markdown",
        reply_markup=home_keyboard()
    )


@router.message(SearchState.waiting_for_query)
async def handle_query(message: Message, state: FSMContext, bot: Bot):
    track_user(message.from_user)

    if not message.text:
        await message.answer(
            "Введите название фильма или сериала текстом.",
            reply_markup=home_keyboard()
        )
        return

    query = message.text.strip()
    if not query:
        await message.answer(
            "Введите название фильма или сериала текстом.",
            reply_markup=home_keyboard()
        )
        return

    log_event(message.from_user.id, "search", query[:120])
    await clear_last_results_keyboard(bot, state, message.chat.id)
    await state.clear()

    searching_msg = await message.answer("⏳ Ищу...")

    try:
        films = await search_movies(query)
    except Exception:
        await searching_msg.delete()
        await message.answer("❌ Сервер временно недоступен. Попробуй чуть позже.")
        return

    await searching_msg.delete()

    if not films:
        await message.answer(
            "😔 Ничего не найдено, попробуй другой запрос.",
            reply_markup=home_keyboard()
        )
        return

    results_message = await message.answer(
        f"🎬 Результаты по запросу *{query}*:",
        parse_mode="Markdown",
        reply_markup=films_keyboard(films, page=0)
    )
    await state.update_data(
        films=films,
        current_page=0,
        results_message_id=results_message.message_id
    )


@router.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    track_user(callback.from_user)
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    films = data.get("films", [])

    if not films:
        await callback.answer("Сделай новый поиск")
        return

    await callback.message.edit_reply_markup(
        reply_markup=films_keyboard(films, page=page)
    )
    await state.update_data(current_page=page)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()
