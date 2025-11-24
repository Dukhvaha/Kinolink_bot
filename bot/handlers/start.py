from aiogram import Router
from aiogram.types import Message
from aiogram.filters import  Command
from aiogram import Bot

from services.zona_parser_service import get_video_url
from bot.file_storage import upload_to_channel

router = Router()

@router.message(Command('film'))
async def film_handler(message: Message, bot: Bot):
    title = message.text.replace("/film", "").strip()

    if not title:
        await message.answer("Использование: /film Название")
        return

    await message.answer(f"Ищу: <b>{title}</b>")

    video_url = await get_video_url(title)

    if not video_url:
        await message.answer("Фильм не найден.")
        return

    await message.answer("Загружаю в хранилище, минутку...")

    file_id = await upload_to_channel(bot, video_url)

    await message.answer_video(
        video=file_id,
        caption=f"Готово. Фильм: {title}"
    )
