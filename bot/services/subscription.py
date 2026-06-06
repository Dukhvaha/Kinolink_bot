from aiogram import Bot

from config import CHANNEL_BOT_ID


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_BOT_ID, user_id)
    except Exception:
        return False

    return member.status not in ("left", "kicked")
