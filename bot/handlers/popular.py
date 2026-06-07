from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.inline import films_keyboard
from bot.keyboards.reply import home_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.movie_service import get_novelties
from bot.services.statistics import log_event, track_user
from bot.services.subscription import is_subscribed

router = Router()


@router.message(F.text == "🔥 Популярное")
async def handle_novelties(message: Message, state: FSMContext, bot: Bot):
    track_user(message.from_user)
    log_event(message.from_user.id, "popular")

    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("Сначала нужна подписка на канал. После этого подборка откроется.")
        return

    await clear_last_results_keyboard(bot, state, message.chat.id)
    msg = await message.answer("Собираю популярное...")

    try:
        films = await get_novelties()
    except Exception:
        await msg.delete()
        await message.answer("Не удалось загрузить подборку. Попробуй чуть позже.")
        return

    await msg.delete()

    if not films:
        await message.answer("Пока ничего не нашел.", reply_markup=home_keyboard())
        return

    films = films[:6]
    results_message = await message.answer(
        "🔥 Сейчас часто смотрят. Выбери фильм:",
        parse_mode="Markdown",
        reply_markup=films_keyboard(films, page=0)
    )
    await state.update_data(
        films=films,
        results_message_id=results_message.message_id
    )
