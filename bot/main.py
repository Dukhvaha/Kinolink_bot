import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_API_TOKEN
from bot.handlers.fallback import router as fallback_router
from bot.handlers.info import router as info_router
from bot.handlers.movie import router as movie_router
from bot.handlers.popular import router as popular_router
from bot.handlers.start import router as start_router
from bot.handlers.search import router as search_router
from bot.handlers.stats import router as stats_router
from bot.handlers.subscription import router as subscription_router
from bot.handlers.video_storage import router as video_storage_router
from bot.services.statistics import init_stats_db
from bot.services.telegram_video_storage import init_telegram_video_db

async def main():
    logging.basicConfig(level=logging.INFO)
    init_stats_db()
    init_telegram_video_db()
    bot = Bot(BOT_API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(video_storage_router)
    dp.include_router(start_router)
    dp.include_router(subscription_router)
    dp.include_router(search_router)
    dp.include_router(movie_router)
    dp.include_router(popular_router)
    dp.include_router(info_router)
    dp.include_router(stats_router)
    dp.include_router(fallback_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
