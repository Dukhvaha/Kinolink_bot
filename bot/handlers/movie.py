from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards.inline import watch_keyboard
from bot.keyboards.reply import home_keyboard
from bot.services.movie_service import build_movie_caption, get_movie, get_poster_photo
from bot.services.statistics import log_event, track_user

router = Router()


@router.callback_query(F.data.startswith("movie_"))
async def handle_movie_select(callback: CallbackQuery, state: FSMContext):
    track_user(callback.from_user)
    movie_id = int(callback.data.split("_")[1])
    log_event(callback.from_user.id, "movie_open", str(movie_id))

    try:
        movie = await get_movie(movie_id)
    except Exception:
        await callback.answer("❌ Что-то пошло не так.", show_alert=True)
        return

    if not movie:
        await callback.answer("Ошибка загрузки фильма", show_alert=True)
        return

    await state.clear()

    poster = movie.get("poster")
    poster_photo = await get_poster_photo(poster)
    caption = build_movie_caption(movie)
    keyboard = watch_keyboard(movie_id)

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
            await callback.message.answer("Выбери способ просмотра:", reply_markup=home_keyboard())
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
            await callback.message.answer("Выбери способ просмотра:", reply_markup=home_keyboard())
            await callback.answer()
            return
        except TelegramBadRequest:
            pass

    await callback.message.answer(
        caption,
        reply_markup=keyboard
    )
    await callback.message.answer("Выбери способ просмотра:", reply_markup=home_keyboard())

    await callback.answer()
