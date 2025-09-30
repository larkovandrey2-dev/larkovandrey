import asyncio
import logging
from email import message
from sqlite3 import SQLITE_READ

import requests
import datetime
import os
import database_scripts
import kbs.inline as inline
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, sticker, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from supabase import create_client, Client
from datetime import date


ADMINS = os.getenv("ADMINS")
logging.basicConfig(level=logging.INFO)
bot = Bot(token="8466015804:AAEt2BWKawjYRbBxhiinKB3JCZaw0-1NMTU")

#Админка - добавлять вопросы,редактировать вопросы,мониторить выходные данные

dp = Dispatcher()
class UserConfig(StatesGroup):
    age = State()
    sex = State()
    education = State()
class Questions(StatesGroup):
    questions = State()
class Admins(StatesGroup):
    edit_question = State()
    new_question = State()
@dp.message(Command('admin'))
async def admin_command(message: types.Message):
    if str(message.from_user.id) in ADMINS:
        builder = await inline.create_admin_commands()
        await message.answer('Доступ разрешен. Выберите действие: ',reply_markup=builder.as_markup())
    else:
        await message.answer('Доступ запрещен.')

@dp.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    if str(call.from_user.id) in ADMINS:
        await call.message.answer('Можете менять вопросики')
        text = 'Текущие вопросы:\n'
        for i in questions:
            text += f'\n{questions.index(i)+1}. {i}'
        builder = await inline.create_edit_questions_kb(questions)
        await call.message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith('question_'))
async def edit_question(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    if data[1] != 'create':
        await call.message.answer('Напиши новый текст для вопроса')
        await state.set_state(Admins.edit_question)
        await state.update_data(question_n = data[1])
    else:
        await call.message.answer('Напиши текст для нового вопроса')
        await state.set_state(Admins.new_question)


@dp.message(Admins.new_question)
async def new_question(message: types.Message, state: FSMContext):
    if type(message.text) == str:
        await message.answer('Вопрос успешно добавлен')
        questions.append(message.text)
        await state.clear()
        await admin_command(message)
@dp.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    if type(message.text) is not str:
        await message.answer('Ай-ай-ай, какой-то неизвестный тип данных')
        return None
    questions[int(question_n)] = message.text
    for id in ADMINS:
        await bot.send_message(id, f'Админы внимание! @{message.from_user.username} изменил вопрос {int(question_n) + 1} на {message.text}')

    await message.answer('Успешно')
    await state.clear()

@dp.callback_query(F.data.startswith('personal_lk'))
async def personal_lk(call: CallbackQuery, state: FSMContext):
    req = f"http://127.0.0.1:8000/api/get_user/{call.from_user.id}"
    data = requests.get(req).json()
    text = f'''Ваш username: @{call.from_user.username}
Ваш ID: {call.message.from_user.id}
Количество пройденных опросов: {data['surveys_count']}\n'''
    if data['role'] == 'user':
        text += 'Ваша роль: пользователь'
    elif data['role'] == 'admin':
        text += 'Ваша роль: администратор'
    elif data['role'] == 'psychologist':
        text += 'Ваша роль: психолог'
    await call.message.answer(text)
@dp.message(Command("start"))
async def start(message: types.Message,state: FSMContext):
    users_id = database_scripts.all_users()
    if str(message.from_user.id) not in 'aa':
        await message.answer('Вы в нашем сервисе впервые. Введите свой возраст')
        await state.set_state(UserConfig.age)
    req = requests.get(f"http://127.0.0.1:8000/api/register_user/{message.from_user.id}")
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Пройти опрос',callback_data='start_test'))
    keyboard.row(types.InlineKeyboardButton(text='Личный кабинет',callback_data='personal_lk'))
    username = message.from_user.username
    if str(message.from_user.id) not in ADMINS:
        text = f'''Добро пожаловать, @{username}, я Mireya. Здесь нет правильных или неправильных ответов - только твои ощущения. Сейчас мне важно лучше узнать, что ты чувствуешь, чтобы увидеть картину твоего душевного состояния. Для этого я предложу короткий опрос. Он очень простой, но с его помощью мы сможем вместе чуть яснее взглянуть на твои эмоции и настроение.'''
        await message.answer(text,reply_markup=keyboard.as_markup())
    if str(message.from_user.id) in ADMINS:
        text = f'''Добро пожаловать, администратор (/admin)'''
        await message.answer(text,reply_markup=keyboard.as_markup())

@dp.message(UserConfig.age)
async def age_setup(message: types.Message, state: FSMContext):
    age = message.text
    if not age.isdigit() or not (12 < int(age) < 100):
        await message.answer('Введите корректный возраст')
    else:
        await state.update_data(age=age)
        kb = ReplyKeyboardMarkup(resize_keyboard=True,keyboard=[[KeyboardButton(text='Мужской 👨')],[KeyboardButton(text='Женский 👩')]])
        await message.answer('Выберите пол:',reply_markup=kb)
        await state.set_state(UserConfig.sex)
@dp.message(UserConfig.sex)
async def sex_setup(message: types.Message, state: FSMContext):
    sex = message.text.split()[0]
    await state.update_data(sex=sex)
    kb = ReplyKeyboardMarkup(resize_keyboard=True,keyboard=[[KeyboardButton(text='Высшее образование')],[KeyboardButton(text='Основное общее образование')],[KeyboardButton(text='Среднее общее')]])
    await message.answer('Выберите уровень образования: ',reply_markup=kb)
    await state.set_state(UserConfig.education)
@dp.message(UserConfig.education)
async def finish_setup(message: types.Message, state: FSMContext):
    education = message.text
    data = await state.get_data()
    print(data,education)

async def ask_question(message: types.Message,state: FSMContext):
    data = await state.get_data()
    print(data)
    question_n = data['question_n']
    question_list = data['question_list']
    await message.answer(question_list[question_n])
async def finish_test(message: types.Message,state: FSMContext):
    await state.clear()
    await message.answer('Опрос заверешен')
@dp.callback_query(F.data.startswith("start_test"))
async def start_test(call: CallbackQuery,state: FSMContext):
    data = requests.get(f"http://127.0.0.1:8000/api/{call.from_user.id}/get_question_list").json()
    questions = data['question_list']
    await state.update_data(question_list=questions)
    await state.update_data(question_n=0)
    await state.set_state(Questions.questions)
    await ask_question(call.message,state)



@dp.message(Questions.questions)
async def message_test(message: types.Message,state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    requests.get(f"http://127.0.0.1:8000/api/add_answer/{message.from_user.id}/{question_n}&{text}&{datetime.datetime.now()}")
    question_n += 1
    if question_n == len(question_list):
        await finish_test(message,state)
    await state.update_data(question_n=question_n)
    await ask_question(message,state)


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
