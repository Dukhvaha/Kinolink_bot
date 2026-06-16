from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import help_keyboard
from bot.services.statistics import log_event, track_user

router = Router()

@router.message(F.text == "🆘 Помощь")
async def handle_help(message:Message):
    track_user(message.from_user)
    log_event(message.from_user.id, "help")

    await message.answer(
        "🆘 *Помощь*\n\n"
        "Выбери сценарий ниже — покажу короткую инструкцию по просмотру.\n\n"
        "Если Mini App капризничает, открывай через браузер: обычно это самый стабильный вариант.",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )


@router.callback_query(F.data == "help_movies")
async def handle_movies_help(callback: CallbackQuery):
    track_user(callback.from_user)
    log_event(callback.from_user.id, "help_movies")

    await callback.message.edit_text(
        "🎬 *Просмотр фильмов*\n\n"
        "1. Нажми 🎬 *Найти фильм*\n"
        "2. Напиши название\n"
        "3. Выбери нужный вариант из списка\n"
        "4. Выбери способ просмотра:\n"
        "• 📱 *Mini App* — быстрый запуск внутри Telegram\n"
        "• 🌐 *В браузере* — стабильнее, если Mini App работает странно\n"
        "• ▶️ *Смотреть в Telegram* — если фильм добавлен в Telegram-базу\n\n"
        "Если доступно несколько озвучек, бот предложит выбрать нужную перед отправкой видео.\n\n"
        "Если проблема сохраняется, свяжитесь с поддержкой 👉 @Sippaks",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_series")
async def handle_series_help(callback: CallbackQuery):
    track_user(callback.from_user)
    log_event(callback.from_user.id, "help_series")

    await callback.message.edit_text(
        "📺 *Просмотр сериалов*\n\n"
        "1. Нажми 🎬 *Найти фильм*\n"
        "2. Напиши название сериала\n"
        "3. Выбери нужный результат\n"
        "4. Выбери способ просмотра:\n"
        "• 📱 *Mini App*\n"
        "• 🌐 *В браузере*\n"
        "• ▶️ *Смотреть в Telegram*\n\n"
        "При просмотре в Telegram бот предложит:\n"
        "• выбрать сезон\n"
        "• выбрать серию\n"
        "• выбрать озвучку\n\n"
        "После отправки серии можно продолжить выбор или включить следующую серию, если она есть в базе.\n\n"
        "Если что-то не грузится:\n"
        "• попробуй открыть через браузер\n"
        "• обнови Telegram\n"
        "• перезапусти приложение\n\n"
        "Если проблема сохраняется, свяжитесь с поддержкой 👉 @Sippaks",
        parse_mode="Markdown",
        reply_markup=help_keyboard()
    )
    await callback.answer()


@router.message(F.text == "📢 Сотрудничество")
async def handle_ads(message:Message):
    track_user(message.from_user)
    log_event(message.from_user.id, "ads")

    await message.answer(
        "📢 *По вопросам сотрудничества*\n\n"
        "Пиши сюда 👉 @Sippaks",
        parse_mode="Markdown"
    )
