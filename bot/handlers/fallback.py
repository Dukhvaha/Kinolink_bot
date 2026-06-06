from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.reply import main_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard

router = Router()


@router.message()
async def handle_unknown_message(message: Message, state: FSMContext, bot: Bot):
    await clear_last_results_keyboard(bot, state, message.chat.id)

    await message.answer(
        "Я не понял эту команду.\n\n"
        "Используй кнопки меню:\n"
        "🎬 *Найти фильм* — поиск фильма или сериала\n"
        "🔥 *Популярное* — подборка популярных фильмов\n"
        "🆘 *Помощь* — инструкция по просмотру",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
