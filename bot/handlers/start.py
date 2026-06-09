# bot/handlers/start.py
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from bot.keyboards.inline import get_subscription_keyboard
from bot.keyboards.reply import main_keyboard
from bot.services.message_cleanup import clear_last_results_keyboard
from bot.services.statistics import log_event, track_user
from bot.services.subscription import is_subscribed

router = Router()


async def send_home(message: Message):
    await message.answer(
        "👋 Добро пожаловать в *KINOLINK | ФИЛЬМЫ И СЕРИАЛЫ*!\n\n"
        "🎬 Здесь ты можешь найти фильм или сериал и смотреть прямо в Telegram.\n\n"
        "Просто выбери нужную кнопку в меню! 🍿",
        parse_mode="Markdown",
        reply_markup=main_keyboard(message.from_user.id in ADMIN_IDS)
    )


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    track_user(message.from_user)
    log_event(message.from_user.id, "start")

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
    track_user(message.from_user)
    log_event(message.from_user.id, "home")
    await clear_last_results_keyboard(bot, state, message.chat.id)
    await state.clear()
    await send_home(message)
