from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.inline import films_keyboard
from bot.keyboards.reply import home_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.movie_service import get_novelties
from bot.services.subscription import is_subscribed

router = Router()


@router.message(F.text == "🔥 Популярное")
async def handle_novelties(message: Message, state: FSMContext, bot: Bot):
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer("❌ Для использования бота подпишитесь на канал!")
        return

    await clear_last_results_keyboard(bot, state, message.chat.id)
    msg = await message.answer("⏳ Загружаю новинки...")

    try:
        films = await get_novelties()
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка загрузки новинок.")
        return

    await msg.delete()

    if not films:
        await message.answer("😔 Новинки не найдены.", reply_markup=home_keyboard())
        return

    films = films[:6]
    results_message = await message.answer(
        "🔥 *Новинки — выбери фильм:*",
        parse_mode="Markdown",
        reply_markup=films_keyboard(films, page=0)
    )
    await message.answer(
        "Для выхода нажми 🏠 *Домой*.",
        parse_mode="Markdown",
        reply_markup=home_keyboard()
    )
    await state.update_data(
        films=films,
        results_message_id=results_message.message_id
    )
