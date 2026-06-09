from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from bot.keyboards.reply import main_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.statistics import log_event, track_user

router = Router()


@router.message()
async def handle_unknown_message(message: Message, state: FSMContext, bot: Bot):
    track_user(message.from_user)
    log_event(message.from_user.id, "unknown_message", (message.text or "")[:120])
    await clear_last_results_keyboard(bot, state, message.chat.id)

    await message.answer(
        "Я не понял эту команду.\n\n"
        "Используй кнопки меню:\n"
        "🎬 *Найти фильм* — поиск фильма или сериала\n"
        "🔥 *Популярное* — подборка популярных фильмов\n"
        "🆘 *Помощь* — инструкция по просмотру",
        parse_mode="Markdown",
        reply_markup=main_keyboard(message.from_user.id in ADMIN_IDS)
    )
