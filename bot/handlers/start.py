from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from bot.keyboards.reply import main_keyboard
from config import CHANNEL_BOT_ID

router = Router()

async def is_subscribed(bot: Bot, user_id:int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_BOT_ID, user_id)
        return member.status not in ('left','kicked')
    except:
        return False


@router.message(CommandStart())
async def cmd_start(message:Message, bot: Bot):
    if not await is_subscribed(bot,message.from_user.id):
        await message.answer(
            "👋 Привет!\n\n"
            "Для использования бота необходимо подписаться на наш канал.\n"
            "После подписки нажми кнопку *Я подписался* ✅",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/KinoLink31")],
                [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
            ])
        )
        return

    await message.answer(
        "👋 Добро пожаловать в *KINOLINK | ФИЛЬМЫ И СЕРИАЛЫ*!\n\n"
        "🎬 Здесь ты можешь найти любой фильм или сериал и смотреть прямо в Telegram.\n\n"
        "📌 *Основные команды:*\n"
        "🎬 *Найти фильм* — поиск по названию\n"
        "🆘 *Помощь* — если что-то не работает\n"
        "📢 *По рекламе* — сотрудничество\n\n"
        "Просто напиши название фильма и я найду его для тебя! 🍿",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data == 'check_sub')
async def check_subscription(callback: CallbackQuery, bot:Bot):
    if await is_subscribed(bot, callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ Подписка подтверждена!\n\n"
            "👋 Добро пожаловать в *KINOLINK | ФИЛЬМЫ И СЕРИАЛЫ*!\n\n"
            "Просто напиши название фильма и я найду его для тебя! 🍿",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
    )
    else:
        await callback.answer(
            "❌ Ты ещё не подписался на канал!",
            show_alert=True
        )