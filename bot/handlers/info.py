from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import help_keyboard

router = Router()

@router.message(F.text == "🆘 Помощь")
async def handle_help(message:Message):
    await message.answer(
        "🆘 *Помощь*\n\n"
        "Выберите, что хотите посмотреть, и я покажу короткую инструкцию.\n\n"
        "Если что-то работает нестабильно, чаще всего помогает открыть контент через браузер.",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )


@router.callback_query(F.data == "help_movies")
async def handle_movies_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎬 *Просмотр фильмов*\n\n"
        "1. Перейдите в раздел 🎬 *Найти фильм*\n"
        "2. Введите название фильма\n"
        "3. Выберите подходящий вариант из списка\n"
        "4. Выберите способ просмотра:\n"
        "• 📱 *Telegram Mini App* — для быстрого запуска внутри Telegram\n"
        "• 🌐 *В браузере* — если Mini App недоступен или работает нестабильно\n\n"
        "После открытия плеера фильм будет доступен для просмотра.\n\n"
        "Если проблема сохраняется, свяжитесь с поддержкой 👉 @Sippaks",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_series")
async def handle_series_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "📺 *Просмотр сериалов*\n\n"
        "1. Откройте раздел 🎬 *Найти фильм*\n"
        "2. Введите название сериала\n"
        "3. Выберите нужный вариант\n"
        "4. Откройте через удобный способ:\n"
        "• 📱 *Telegram Mini App*\n"
        "• 🌐 *Браузер*\n"
        "5. В плеере выберите источник *Vibix*\n"
        "6. Укажите сезон и серию\n\n"
        "*Если возникли сложности*\n\n"
        "• Рекомендуем открыть контент через браузер — это наиболее стабильный вариант\n"
        "• Убедитесь, что у вас установлена актуальная версия Telegram\n"
        "• Перезапустите приложение и повторите попытку\n\n"
        "Если проблема сохраняется, свяжитесь с поддержкой 👉 @Sippaks",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )
    await callback.answer()


@router.message(F.text == "📢 По рекламе")
async def handle_ads(message:Message):
    await message.answer(
        "📢 *По вопросам рекламы*\n\n"
        "Пиши сюда 👉 @Sippaks",
        parse_mode="Markdown"
    )