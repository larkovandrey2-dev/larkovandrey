import asyncio
import logging
import requests
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
questions = ['Question 1', 'Question 2', 'Question 3', 'Question 4', 'Question 5']
logging.basicConfig(level=logging.INFO)
bot = Bot(token="8466015804:AAEt2BWKawjYRbBxhiinKB3JCZaw0-1NMTU")
dp = Dispatcher()
class Questions(StatesGroup):
    question = State()
@dp.message(Command("start"))
async def start(message: types.Message):
    req = requests.get(f"http://127.0.0.1:8000/api/register_user/{message.from_user.id}")
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Пройти опрос',callback_data='start_test'))
    username = message.from_user.username
    text = f'''Добро пожаловать, @{username}, я Mireya. Здесь нет правильных или неправильных ответов - только твои ощущения. Сейчас мне важно лучше узнать, что ты чувствуешь, чтобы увидеть картину твоего душевного состояния. Для этого я предложу короткий опрос. Он очень простой, но с его помощью мы сможем вместе чуть яснее взглянуть на твои эмоции и настроение.'''
    await message.answer(text,reply_markup=keyboard.as_markup())


async def ask_question(message: types.Message,state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    await message.answer(questions[question_n-1])
async def finish_test(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer('Test is over')
@dp.callback_query(F.data.startswith("start_test"))
async def start_test(call: CallbackQuery,state: FSMContext):
    await call.message.delete()
    await bot.send_message(call.message.chat.id,questions[0])
    await state.set_state(Questions.question)
    await state.update_data(question_n=1)
@dp.message(Questions.question)
async def message_test(message: types.Message,state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    req = requests.get(f"http://127.0.0.1:8000/api/add_answer/{message.from_user.id}/{question_n}&{text}&{datetime.datetime.now()}")
    question_n += 1
    if question_n == len(questions)+1:
        await finish_test(message,state)
        return None
    await state.update_data(question_n=question_n)
    await ask_question(message,state)
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
