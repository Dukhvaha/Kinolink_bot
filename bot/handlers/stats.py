from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from bot.services.statistics import get_stats_report

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def handle_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Статистика доступна только администраторам.")
        return

    await message.answer(get_stats_report(), parse_mode="Markdown")
