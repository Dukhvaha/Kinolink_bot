from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.inline import films_keyboard, watch_keyboard
from bot.keyboards.reply import home_keyboard
from bot.services.message_cleanup import clear_after_card_message
from bot.services.movie_service import build_movie_caption, get_movie, get_poster_photo
from bot.services.statistics import log_event, track_user
from bot.services.telegram_video_storage import (
    get_available_episodes,
    get_available_seasons,
    get_episode_voiceovers,
    get_movie_voiceovers,
    get_next_episode_record,
    get_telegram_video_by_id,
    send_video_record_to_user,
)

router = Router()

AFTER_CARD_TEXT = (
    "🍿 Приятного просмотра! Чтобы вернуться в меню — нажми 🏠 Домой.\n\n"
    "Если Mini App капризничает, не разворачивает видео или работает нестабильно, "
    "открой фильм через браузер — так обычно надежнее."
)


def voiceover_keyboard(records, back_callback: str | None = None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎧 {record['voiceover']}",
                callback_data=f"tg_send_{record['id']}",
            )
        ]
        for record in records
    ]

    if back_callback:
        buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def seasons_keyboard(imdb_id: str, seasons: list[int]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{season} сезон",
                    callback_data=f"tg_season_{imdb_id}_{season}",
                )
            ]
            for season in seasons
        ]
    )


def episodes_keyboard(imdb_id: str, season: int, episodes: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{episode} серия",
                callback_data=f"tg_episode_{imdb_id}_{season}_{episode}",
            )
        ]
        for episode in episodes
    ]
    buttons.append([InlineKeyboardButton(text="↩️ Назад к сезонам", callback_data=f"tg_back_seasons_{imdb_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def after_send_keyboard(record) -> InlineKeyboardMarkup | None:
    buttons = []

    if record["content_type"] == "series":
        buttons.append([
            InlineKeyboardButton(
                text="▶️ Продолжить выбор",
                callback_data=f"tg_back_episodes_{record['imdb_id']}_{record['season']}",
            )
        ])

        next_record = get_next_episode_record(record)
        if next_record:
            buttons.append([
                InlineKeyboardButton(
                    text="⏭ Следующая серия",
                    callback_data=f"tg_send_{next_record['id']}",
                )
            ])
    elif record["content_type"] == "movie":
        buttons.append([
            InlineKeyboardButton(
                text="▶️ Продолжить выбор",
                callback_data="back_to_results",
            )
        ])

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_after_card_hint(callback: CallbackQuery, state: FSMContext):
    message = await callback.message.answer(
        AFTER_CARD_TEXT,
        reply_markup=home_keyboard()
    )
    await state.update_data(after_card_message_id=message.message_id)


@router.callback_query(F.data.startswith("movie_"))
async def handle_movie_select(callback: CallbackQuery, state: FSMContext):
    track_user(callback.from_user)
    parts = callback.data.split("_")
    if len(parts) == 2:
        media_type = "movie"
        movie_id = int(parts[1])
    else:
        media_type = parts[1]
        movie_id = int(parts[2])

    log_event(callback.from_user.id, "movie_open", f"{media_type}:{movie_id}")

    try:
        movie = await get_movie(movie_id, media_type)
    except Exception:
        await callback.answer("❌ Что-то пошло не так.", show_alert=True)
        return

    if not movie:
        await callback.answer("Ошибка загрузки фильма", show_alert=True)
        return

    poster = movie.get("poster")
    poster_photo = await get_poster_photo(poster)
    caption = build_movie_caption(movie)
    keyboard = watch_keyboard(movie_id, media_type, movie.get("imdb_id"))

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

    if poster_photo:
        try:
            await callback.message.answer_photo(
                photo=poster_photo,
                caption=caption,
                reply_markup=keyboard
            )
            await send_after_card_hint(callback, state)
            await callback.answer()
            return
        except TelegramBadRequest:
            pass

    if poster:
        try:
            await callback.message.answer_photo(
                photo=poster,
                caption=caption,
                reply_markup=keyboard
            )
            await send_after_card_hint(callback, state)
            await callback.answer()
            return
        except TelegramBadRequest:
            pass

    await callback.message.answer(
        caption,
        reply_markup=keyboard
    )
    await send_after_card_hint(callback, state)

    await callback.answer()


@router.callback_query(F.data == "back_to_results")
async def handle_back_to_results(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    films = data.get("films", [])
    page = int(data.get("current_page") or 0)

    if not films:
        await callback.answer("Список уже сброшен. Сделай новый поиск.", show_alert=True)
        return

    await clear_after_card_message(bot, state, callback.message.chat.id)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

    results_message = await callback.message.answer(
        "🎬 Вернулся к выбору:",
        reply_markup=films_keyboard(films, page=page),
    )
    await state.update_data(results_message_id=results_message.message_id)
    await callback.answer()


@router.callback_query(F.data == "watch_tg_missing")
async def handle_telegram_watch_missing(callback: CallbackQuery):
    track_user(callback.from_user)
    log_event(callback.from_user.id, "telegram_watch_missing", "missing_imdb")
    await callback.message.answer(
        "Извини, этот фильм пока нельзя открыть прямо в Telegram.\n\n"
        "Попробуй Mini App или браузер. Если хочешь уточнить по добавлению — напиши @Sippaks."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("watch_tg_"))
async def handle_telegram_watch(callback: CallbackQuery, bot: Bot):
    track_user(callback.from_user)
    payload = callback.data.removeprefix("watch_tg_")
    parts = payload.split("_", 1)
    if len(parts) != 2:
        await callback.answer("Не удалось открыть Telegram-версию.", show_alert=True)
        return

    media_type, imdb_id = parts
    content_type = "series" if media_type == "tv" else "movie"
    log_event(callback.from_user.id, "telegram_watch", f"{content_type}:{imdb_id}")

    await callback.answer("Проверяю Telegram-версию...")

    if content_type == "movie":
        records = get_movie_voiceovers(imdb_id)
        if not records:
            await callback.message.answer(
                "Извини, этого фильма пока нет в Telegram-базе.\n\n"
                "Можно открыть его через Mini App или браузер. Если хочешь попросить добавить фильм — напиши @Sippaks."
            )
            return

        await callback.message.answer(
            "🎧 Выбери озвучку:",
            reply_markup=voiceover_keyboard(records, back_callback="back_to_results"),
        )
        return

    seasons = get_available_seasons(imdb_id)
    if not seasons:
        await callback.message.answer(
            "Извини, этого сериала пока нет в Telegram-базе.\n\n"
            "Можно открыть его через Mini App или браузер. Если хочешь попросить добавить сериал — напиши @Sippaks."
        )
        return

    try:
        await callback.message.edit_text(
            "📺 Выбери сезон:",
            reply_markup=seasons_keyboard(imdb_id, seasons),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "📺 Выбери сезон:",
            reply_markup=seasons_keyboard(imdb_id, seasons),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg_season_"))
async def handle_telegram_season(callback: CallbackQuery):
    track_user(callback.from_user)
    payload = callback.data.removeprefix("tg_season_")
    try:
        imdb_id, season_value = payload.rsplit("_", 1)
        season = int(season_value)
    except ValueError:
        await callback.answer("Не удалось выбрать сезон.", show_alert=True)
        return

    episodes = get_available_episodes(imdb_id, season)
    if not episodes:
        await callback.answer("В этом сезоне пока нет доступных серий.", show_alert=True)
        return

    log_event(callback.from_user.id, "telegram_season", f"{imdb_id}:{season}")
    try:
        await callback.message.edit_text(
            f"📺 {season} сезон. Выбери серию:",
            reply_markup=episodes_keyboard(imdb_id, season, episodes),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📺 {season} сезон. Выбери серию:",
            reply_markup=episodes_keyboard(imdb_id, season, episodes),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg_episode_"))
async def handle_telegram_episode(callback: CallbackQuery):
    track_user(callback.from_user)
    payload = callback.data.removeprefix("tg_episode_")
    try:
        imdb_id, season_value, episode_value = payload.rsplit("_", 2)
        season = int(season_value)
        episode = int(episode_value)
    except ValueError:
        await callback.answer("Не удалось выбрать серию.", show_alert=True)
        return

    records = get_episode_voiceovers(imdb_id, season, episode)
    if not records:
        await callback.answer("Эта серия пока недоступна.", show_alert=True)
        return

    log_event(callback.from_user.id, "telegram_episode", f"{imdb_id}:{season}:{episode}")
    try:
        await callback.message.edit_text(
            f"🎧 {season} сезон, {episode} серия. Выбери озвучку:",
            reply_markup=voiceover_keyboard(records, back_callback=f"tg_back_episodes_{imdb_id}_{season}"),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"🎧 {season} сезон, {episode} серия. Выбери озвучку:",
            reply_markup=voiceover_keyboard(records, back_callback=f"tg_back_episodes_{imdb_id}_{season}"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg_back_seasons_"))
async def handle_telegram_back_seasons(callback: CallbackQuery):
    imdb_id = callback.data.removeprefix("tg_back_seasons_")
    seasons = get_available_seasons(imdb_id)
    if not seasons:
        await callback.answer("Сезоны пока недоступны.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "📺 Выбери сезон:",
            reply_markup=seasons_keyboard(imdb_id, seasons),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "📺 Выбери сезон:",
            reply_markup=seasons_keyboard(imdb_id, seasons),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg_back_episodes_"))
async def handle_telegram_back_episodes(callback: CallbackQuery):
    payload = callback.data.removeprefix("tg_back_episodes_")
    try:
        imdb_id, season_value = payload.rsplit("_", 1)
        season = int(season_value)
    except ValueError:
        await callback.answer("Не удалось вернуться к сериям.", show_alert=True)
        return

    episodes = get_available_episodes(imdb_id, season)
    if not episodes:
        await callback.answer("Серии пока недоступны.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            f"📺 {season} сезон. Выбери серию:",
            reply_markup=episodes_keyboard(imdb_id, season, episodes),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📺 {season} сезон. Выбери серию:",
            reply_markup=episodes_keyboard(imdb_id, season, episodes),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg_send_"))
async def handle_telegram_send(callback: CallbackQuery, bot: Bot):
    track_user(callback.from_user)
    try:
        record_id = int(callback.data.removeprefix("tg_send_"))
    except ValueError:
        await callback.answer("Не удалось отправить видео.", show_alert=True)
        return

    log_event(callback.from_user.id, "telegram_send_attempt", str(record_id))
    await callback.answer("Отправляю видео...")
    record = get_telegram_video_by_id(record_id)
    sent = await send_video_record_to_user(bot, callback.message.chat.id, record_id)
    if not sent:
        await callback.message.answer("Не удалось отправить Telegram-видео. Попробуй Mini App или браузер.")
        return

    log_event(callback.from_user.id, "telegram_video_sent", str(record_id))

    if record:
        keyboard = after_send_keyboard(record)
        if keyboard:
            await callback.message.answer(
                "Готово. Что дальше?",
                reply_markup=keyboard,
            )
