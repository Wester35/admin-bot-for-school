import asyncio
import logging
from aiogram import Bot, Dispatcher, F

from app.handlers import base, news, schedule
from config import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(base.router)
    dp.include_router(news.router)
    dp.include_router(schedule.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info("Starting bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')