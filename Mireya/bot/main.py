import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN
from bot.handlers import user, admin, survey, start, llm_talk
from helpers.database import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(start.router)
dp.include_router(user.router)
dp.include_router(survey.router)
dp.include_router(llm_talk.router)
dp.include_router(admin.router)


async def on_startup():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    if supabase_url and supabase_key:
        db = DatabaseService(supabase_url, supabase_key)
        await db.create_client()
        logging.info("Database initialized")


async def main():
    await on_startup()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())