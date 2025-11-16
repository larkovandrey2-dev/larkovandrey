import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from bot.config import BOT_TOKEN,WEBHOOK_PATH,WEBHOOK_URL
from bot.handlers import user,admin,survey,start, llm_talk
from fastapi import FastAPI, Request

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(survey.router)
dp.include_router(llm_talk.router)



app = FastAPI()
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook set:", WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def webhook(update: dict):
    tg_update = Update.model_validate(update)
    await dp.feed_update(bot, tg_update)
    return {"ok": True}
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080,reload=False)



if __name__ == '__main__':
    main()