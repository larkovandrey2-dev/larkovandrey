import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user,admin,survey,start

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(survey.router)
dp.include_router(start.router)

async def main():
    await dp.start_polling(bot,skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())