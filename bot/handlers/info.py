from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "🆘 Помощь")
async def handle_help(message:Message):
    await message.answer(
        "🆘 *Помощь*\n\n"
        "1. Нажми кнопку 🎬 *Найти фильм*\n"
        "2. Введи название фильма или сериала\n"
        "3. Выбери нужный вариант из списка\n"
        "4. Нажми 📱 *Смотреть в Telegram* или 🌐 *В браузере*\n\n"
        "Если что-то не работает — напиши сюда 👉 @Sippaks",
        parse_mode="Markdown"
    )

@router.message(F.text == "📢 По рекламе")
async def handle_ads(message:Message):
    await message.answer(
        "📢 *По вопросам рекламы*\n\n"
        "Пиши сюда 👉 @Sippaks",
        parse_mode="Markdown"
    )
