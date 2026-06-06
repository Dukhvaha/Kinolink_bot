# bot/handlers/start.py
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_subscription_keyboard
from bot.keyboards.reply import main_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.subscription import is_subscribed

router = Router()


async def send_home(message: Message):
    await message.answer(
        "👋 Добро пожаловать в *KINOLINK | ФИЛЬМЫ И СЕРИАЛЫ*!\n\n"
        "🎬 Здесь ты можешь найти любой фильм или сериал и смотреть прямо в Telegram.\n\n"
        "Просто выбери нужную кнопку в меню! 🍿",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer(
            "👋 Привет!\n\n"
            "Для использования бота необходимо подписаться на наш канал.\n"
            "После подписки нажми кнопку *Я подписался* ✅",
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard()
        )
        return

    await send_home(message)


@router.message(F.text == "🏠 Домой")
async def handle_home(message: Message, state: FSMContext, bot: Bot):
    await clear_last_results_keyboard(bot, state, message.chat.id)
    await state.clear()
    await send_home(message)

