import asyncio
import logging
import datetime
import os
from email import message

import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton
import database_scripts
import kbs.inline as inline
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, sticker, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from supabase import create_client, Client
from datetime import date

import scripts

ADMINS = os.getenv("ADMINS")
logging.basicConfig(level=logging.INFO)
bot = Bot(token="8466015804:AAEt2BWKawjYRbBxhiinKB3JCZaw0-1NMTU")

# Админка - добавлять вопросы,редактировать вопросы,мониторить выходные данные

dp = Dispatcher()

class UserChanges(StatesGroup):
    age = State()
    education = State()
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
        await message.answer('Доступ разрешен. Выберите действие: ', reply_markup=builder.as_markup())
    else:
        await message.answer('Доступ запрещен.')


@dp.callback_query(F.data.startswith('admin_delete_questions'))
async def admin_delete_questions_list(call: CallbackQuery):
    questions = await database_scripts.all_questions()
    kb = await inline.create_deletion_question_list(questions)
    await call.message.answer('Выберите из списка вопрос, который хотите удалить:', reply_markup=kb.as_markup())


@dp.callback_query(F.data.startswith('delete_question'))
async def delete_question(call: CallbackQuery):
    await call.message.delete()
    data = call.data.split('_')
    survey_index = int(data[2])
    question_index = int(data[3])
    await database_scripts.delete_question(question_index, survey_index)
    async with aiohttp.ClientSession() as session:
        response = await session.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}")
        response = await response.json()
        response = response["data"]
    if response:
        first_question_index = int(response[0]['question_index'])
        for i in range(1, len(response)):
            await database_scripts.change_question_index(int(response[i]['question_index']),
                                                         int(response[i]['survey_index']),
                                                         first_question_index + i + 1)
    await call.message.answer('Удаление успешно')
    await admin_delete_questions_list(call)


@dp.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    if str(call.from_user.id) in ADMINS:
        questions = await database_scripts.all_questions()
        kb = await inline.create_edit_questions_kb(questions)
        await call.message.answer(
            'Ниже представлена информация в виде: номер опроса || текст вопроса. Можете менять вопросы и создавать новые',
            reply_markup=kb.as_markup())


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
        async with aiohttp.ClientSession() as session:
            response = await session.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}")
            response = await response.json()
        if response['data']:
            quest_index = response['data'][-1]['question_index'] + 1

    except Exception as e:
        print(e)
    await database_scripts.add_question(quest_index, survey_index, quest_text)
    await state.clear()
    await admin_command(message)


@dp.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    edited_question = message.text
    data = await state.get_data()
    await database_scripts.change_question(int(data['question_index']), int(data['survey_index']), edited_question)
    await message.answer('Успешно изменен вопрос')
    await admin_command(message)


@dp.callback_query(F.data.startswith('personal_lk'))
async def personal_lk(call: CallbackQuery):
    req = f"http://127.0.0.1:8000/api/get_user/{call.from_user.id}"
    async with aiohttp.ClientSession() as session:
        data = await session.get(req)
        data = await data.json()
    text = f'''*Профиль пользователя @{call.from_user.username}*\n
🆔: {call.message.from_user.id}\n
Пройдено опросов ✔️: {data['surveys_count']}\n
Пол: {'👨' if data['sex'] == 'Мужской' else '👩'}\n
Возраст: {data['age']}\n
Образование 🎓: {data['education']}\n\n'''
    if data['role'] == 'user':
        text += 'Ваша роль: пользователь'
    elif data['role'] == 'admin':
        text += 'Ваша роль: администратор'
    elif data['role'] == 'psychologist':
        text += 'Ваша роль: психолог'
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Изменить возраст",callback_data="lk_change_age"))
    builder.row(InlineKeyboardButton(text="Изменить пол",callback_data="lk_change_sex"))
    builder.row(InlineKeyboardButton(text="Изменить образование",callback_data="lk_change_education"))
    await call.message.answer(text,parse_mode=ParseMode.MARKDOWN,reply_markup=builder.as_markup())
@dp.callback_query(F.data.startswith('lk_change_sex'))
async def lk_change_sex(call: CallbackQuery):
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    sex = user_data['sex']
    if sex == 'Мужской':
        await database_scripts.change_user_stat(int(call.from_user.id), 'sex','Женский')
    else:
        await database_scripts.change_user_stat(int(call.from_user.id), 'sex', 'Мужской')
    await call.message.delete()
    await personal_lk(call)


@dp.callback_query(F.data.startswith('lk_change_age'))
async def lk_change_age(call: CallbackQuery,state: FSMContext):
    await call.message.delete()
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    await call.message.answer("Введите свой возраст: ")
    await state.set_state(UserChanges.age)
    await state.update_data(callback=call)
@dp.message(UserChanges.age)
async def lk_change_age_commit(message: types.Message,state: FSMContext):
    age = message.text
    data = await state.get_data()
    if not age.isdecimal() or not(16 < int(age) < 100):
        await message.answer('Введите корректный возраст: ')
    else:
        await database_scripts.change_user_stat(message.from_user.id, 'age', int(age))
        await personal_lk(data['callback'])
        await state.clear()
@dp.callback_query(F.data.startswith('lk_change_education'))
async def lk_change_education(call: CallbackQuery,state: FSMContext):
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await call.message.delete()
    await call.message.answer('Выберите уровень образования: ',reply_markup=kb)
    await state.set_state(UserChanges.education)
    await state.update_data(callback=call)
@dp.message(UserChanges.education)
async def lk_change_education_commit(message: types.Message,state: FSMContext):
    education = message.text
    data = await state.get_data()
    if education not in ['Высшее образование','Основное общее образование','Среднее общее']:
        await message.answer('Выберите корректный уровень образования: ')
    else:
        await database_scripts.change_user_stat(message.from_user.id, 'education', education)
        await message.answer('Изменение успешно!',reply_markup=types.ReplyKeyboardRemove())
        await personal_lk(data['callback'])
        await state.clear()
@dp.message(F.text == "Назад 🔙")
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    if message.from_user.id not in await database_scripts.all_users():
        await message.answer('Вы в нашем сервисе впервые. Введите свой возраст')
        await state.set_state(UserConfig.age)
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(types.InlineKeyboardButton(text='Пройти опрос', callback_data='start_test'))
        keyboard.row(types.InlineKeyboardButton(text='Личный кабинет', callback_data='personal_lk'))
        username = message.from_user.username
        if str(message.from_user.id) not in ADMINS:
            text = f'''Добро пожаловать, @{username}, я Mireya. Здесь нет правильных или неправильных ответов - только твои ощущения. Сейчас мне важно лучше узнать, что ты чувствуешь, чтобы увидеть картину твоего душевного состояния. Для этого я предложу короткий опрос. Он очень простой, но с его помощью мы сможем вместе чуть яснее взглянуть на твои эмоции и настроение.'''
            await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        if str(message.from_user.id) in ADMINS:
            text = f'''Добро пожаловать, администратор (/admin)'''
            await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await message.answer('Выберите действие: ', reply_markup=keyboard.as_markup())


@dp.message(UserConfig.age)
async def age_setup(message: types.Message, state: FSMContext):
    age = message.text
    if not age.isdigit() or not (14 < int(age) < 100):
        await message.answer('Введите корректный возраст')
    else:
        await state.update_data(age=age)
        kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                 keyboard=[[KeyboardButton(text='Мужской 👨')], [KeyboardButton(text='Женский 👩')]])
        await message.answer('Выберите пол:', reply_markup=kb)
        await state.set_state(UserConfig.sex)


@dp.message(UserConfig.sex)
async def sex_setup(message: types.Message, state: FSMContext):
    sex = message.text.split()[0]
    await state.update_data(sex=sex)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await message.answer('Выберите уровень образования: ', reply_markup=kb)
    await state.set_state(UserConfig.education)


@dp.message(UserConfig.education)
async def finish_setup(message: types.Message, state: FSMContext):
    education = message.text
    data = await state.get_data()
    sex = data['sex'].split()[0]
    age = data['age']
    if education not in ['Высшее образование','Основное общее образование','Среднее общее']:
        await message.answer('Выберите корректный уровень образования: ')
    else:
        if str(message.from_user.id) in ADMINS:
            await database_scripts.create_user(message.from_user.id, 'admin', 0)
        else:
            await database_scripts.create_user(message.from_user.id, 'user', 0)
        await database_scripts.change_user_stat(message.from_user.id, 'education', education)
        await database_scripts.change_user_stat(message.from_user.id, 'sex', sex)
        await database_scripts.change_user_stat(message.from_user.id, 'age', int(age))
        await start(message, state)


async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    current_question = [i['question_text'] for i in question_list if i['question_index'] == question_n][0]
    await message.answer(current_question)


async def finish_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    survey_n = data['question_list'][0]['survey_index']
    user_data = await database_scripts.get_user_stats(message.from_user.id)
    global_n = data['global_n']
    surveys_user_c = user_data['surveys_count']
    results_list = user_data['all_user_global_attempts']
    if results_list is None:
        results_list = []
    results_list.append(global_n)
    if surveys_user_c is None:
        surveys_user_c = 0
    await database_scripts.change_user_stat(message.from_user.id, 'last_survey_index', survey_n)
    await database_scripts.change_user_stat(message.from_user.id, 'surveys_count', surveys_user_c + 1)
    await database_scripts.change_user_stat(message.from_user.id, 'all_user_global_attempts', results_list)
    await state.clear()
    await message.answer('Опрос заверешен. Твои ответы получены, и сейчас ты увидишь свой уровень стресса/тревожности')
    user_answers = await database_scripts.get_answers_by_global_attempt(int(global_n))
    user_answers.sort(key=lambda x: x['question_index'])
    user_answers = [i['response_text'] for i in user_answers]
    ans_form = await scripts.form_gad7_survey_1(user_answers, user_data['sex'], user_data['age'],
                                                user_data['education'])
    predicted_level = await scripts.predict_stress_level(ans_form)
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🔙')]],resize_keyboard=True)
    await message.answer(f'Предполагаемый уровень стресса/тревожности: {predicted_level}%', reply_markup=kb)
    await database_scripts.add_survey_result(message.from_user.id, global_n, survey_n,
                                             str(datetime.datetime.now().strftime('%Y-%M-%D %H:%M:%S')),
                                             predicted_level)


@dp.callback_query(F.data.startswith("start_test"))
async def start_test(call: CallbackQuery, state: FSMContext):
    await state.clear()
    async with aiohttp.ClientSession() as session:
        data = await session.get(f"http://127.0.0.1:8000/api/{call.from_user.id}/get_question_list")
        data = await data.json()
    global_surveys_n = list(set(await database_scripts.all_global_attempts()))
    global_surveys_n.sort()
    if not global_surveys_n:
        global_surveys_n = [0]
    await state.update_data(question_list=data)
    await state.update_data(question_n=1)
    await state.update_data(global_n=global_surveys_n[-1] + 1)
    await state.set_state(Questions.questions)
    await ask_question(call.message, state)


@dp.message(Questions.questions)
async def message_test(message: types.Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    global_n = data['global_n']
    survey_n = question_list[0]['survey_index']
    async with aiohttp.ClientSession() as session:
        await session.get(
            f"http://127.0.0.1:8000/api/add_question/{message.from_user.id}&{survey_n}&{question_n}&{text}&{global_n}&{datetime.datetime.now()}")
    if question_n == len(question_list):
        await finish_test(message, state)
        return None
    question_n += 1
    await state.update_data(question_n=question_n)
    await ask_question(message, state)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
