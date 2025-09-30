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
@dp.callback_query(F.data.startswith('admin_delete_questions'))
async def admin_delete_questions_list(call: CallbackQuery):
    await call.message.delete()
    questions = database_scripts.all_questions()
    kb = await inline.create_deletion_question_list(questions)
    await call.message.answer('Выберите из списка вопрос, который хотите удалить:',reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith('delete_question'))
async def delete_question(call: CallbackQuery):
    await call.message.delete()
    data = call.data.split('_')
    survey_index = int(data[2])
    question_index = int(data[3])
    database_scripts.delete_question(question_index, survey_index)
    response = requests.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}").json()['data']
    if response:
        first_question_index = int(response[0]['question_index'])
        for i in range(1,len(response)):
            database_scripts.change_question_index(int(response[i]['question_index']), int(response[i]['survey_index']),first_question_index+i+1)
    await call.message.answer('Удаление успешно')
    await admin_show_questions_actions(call)

@dp.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    if str(call.from_user.id) in ADMINS:
        questions = database_scripts.all_questions()
        kb = await inline.create_edit_questions_kb(questions)
        await call.message.answer('Ниже представлена информация в виде: номер опроса || текст вопроса. Можете менять вопросы и создавать новые',reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith('new_question'))
async def new_question_start(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Введите новый текст для вопроса в формате: номер опроса | текст вопроса')
    await state.set_state(Admins.new_question)
@dp.callback_query(F.data.startswith('change_question'))
async def edit_question(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    survey_index = data[2]
    question_index = data[3]
    await call.message.answer(f'Введите новый текст для вопроса {question_index} из опроса {survey_index}')
    await state.update_data(question_index=question_index)
    await state.update_data(survey_index=survey_index)
    await state.set_state(Admins.edit_question)


@dp.message(Admins.new_question)
async def new_question(message: types.Message, state: FSMContext):
    msg = message.text.split('|')
    survey_index = int(msg[0])
    quest_text = msg[1]
    quest_index = 1
    try:
        response = requests.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}").json()
        if response['data']:
            quest_index = response['data'][-1]['question_index'] + 1

    except Exception as e:
        print(e)
    database_scripts.add_question(quest_index, survey_index, quest_text)
    await state.clear()
    await admin_command(message)
@dp.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    edited_question = message.text
    data = await state.get_data()
    database_scripts.change_question(int(data['question_index']),int(data['survey_index']),edited_question)
    await message.answer('Успешно изменен вопрос')
    await admin_command(message)

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
    if message.from_user.id not in database_scripts.all_users():
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
    database_scripts.create_user(message.from_user.id,'user',0)

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
