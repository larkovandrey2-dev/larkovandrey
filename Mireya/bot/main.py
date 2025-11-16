import asyncio
import logging
from contextlib import asynccontextmanager
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiohttp import web

from bot.config import BOT_TOKEN,WEBHOOK_PATH,WEBHOOK_URL
from bot.handlers import user,admin,survey,start, llm_talk
from fastapi import FastAPI, Request
PORT = int(getenv("PORT"))
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(survey.router)
dp.include_router(llm_talk.router)



# API
routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    """Используется для health check"""
    return web.Response(text="OK")


@routes.post(f"/{BOT_TOKEN}")
async def handle_webhook_request(request):
    """Обрабатывает webhook из telegram"""

    # Достаем токен
    url = str(request.url)
    index = url.rfind("/")
    token = url[index + 1 :]

    # Проверяем токен
    if token == BOT_TOKEN:
        request_data = await request.json()
        update = types.Update(**request_data)
        await dp._process_update(bot=bot, update=update)

        return web.Response(text="OK")
    else:
        return web.Response(status=403)


if __name__ == "__main__":

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host="0.0.0.0", port=PORT)