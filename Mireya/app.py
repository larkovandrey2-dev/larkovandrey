import asyncio
import logging
import requests
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder


logging.basicConfig(level=logging.INFO)
bot = Bot(token="8466015804:AAEt2BWKawjYRbBxhiinKB3JCZaw0-1NMTU")
dp = Dispatcher()
class Questions(StatesGroup):
    question = State()
    answer = State()



@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Пройти опрос',callback_data='start_test'))
    username = message.from_user.username
    text = f'''Добро пожаловать, @{username}, я Mireya. Здесь нет правильных или неправильных ответов - только твои ощущения. Сейчас мне важно лучше узнать, что ты чувствуешь, чтобы увидеть картину твоего душевного состояния. Для этого я предложу короткий опрос. Он очень простой, но с его помощью мы сможем вместе чуть яснее взглянуть на твои эмоции и настроение.'''
    await message.answer(text,reply_markup=keyboard.as_markup())



@dp.callback_query(F.data.startswith("start_test"))
async def start_test(call):
    await call.message.delete()
    await bot.send_message(call.message.chat.id,'Write smth')

@dp.message()
async def message_test(message: types.Message):
    text = message.text
    req = requests.get(f'http://127.0.0.1:8000/api/add_answer/{message.from_user.id}&{text}&{datetime.datetime.now()}')
    print(req.text)
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
