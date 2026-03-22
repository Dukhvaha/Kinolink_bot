import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import API_TOKEN


async  def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
