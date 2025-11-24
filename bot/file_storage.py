from aiogram import Bot
from aiogram.types import FSInputFile
from services.downloader import download_video
from config import CHANNEL_ID
import os

TEMP_PATH = "/tmp/video.mp4"

async def upload_to_channel(bot: Bot, video_url: str) -> str:
    """
    Скачивает видео, заливает в канал, возвращает file_id
    """

    path = await download_video(video_url, TEMP_PATH)

    message = await bot.send_video(
        chat_id=CHANNEL_ID,
        video=FSInputFile(path),
        caption="Автозагрузка"
    )

    file_id = message.video.file_id

    # можешь удалять файл — он уже не нужен
    if os.path.exists(path):
        os.remove(path)

    return file_id
