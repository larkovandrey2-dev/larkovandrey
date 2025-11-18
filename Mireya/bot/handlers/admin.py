import os
from datetime import datetime

from aiogram import Router, types, F
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from watchfiles import awatch

from bot.config import ADMINS
from bot.states import UserConfig, UserChanges, Questions, Admins
from bot.services.database import DatabaseService
from bot.utils import gad7_predict as gad7
from bot.utils.kbs import inline
import bot.services.api as api

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()
@router.message(F.text == 'Назад 🛡️')
@router.message(Command('admin'))
async def admin_command(message: types.Message,state: FSMContext):
    await state.clear()
    await db.create_client()
    user_data = await db.get_user_stats(int(message.from_user.id))
    user_role = user_data['role']
    print(user_role)
    if "admin" in user_role:
        builder = await inline.create_admin_commands(user_role)
        await message.answer('Доступ разрешен. Выберите действие: ', reply_markup=builder.as_markup())
    else:
        await message.answer('Доступ запрещен.')


@router.callback_query(F.data.startswith('admin_delete_questions'))
async def admin_delete_questions_list(call: CallbackQuery):
    await db.create_client()
    questions = await db.all_questions()
    kb = await inline.create_deletion_question_list(questions)
    await call.message.answer('Выберите из списка вопрос, который хотите удалить:', reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith('delete_question'))
async def delete_question(call: CallbackQuery):
    await db.create_client()
    await call.message.delete()
    data = call.data.split('_')
    survey_index = int(data[2])
    question_index = int(data[3])
    await db.delete_question(question_index, survey_index)
    response = await api.get_questions(survey_index)
    if response:
        first_question_index = int(response[0]['question_index'])
        for i in range(1, len(response)):
            await db.change_question_index(int(response[i]['question_index']),
                                                         int(response[i]['survey_index']),
                                                         first_question_index + i + 1)
    await call.message.answer('Удаление успешно')
    await admin_delete_questions_list(call)


@router.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    await db.create_client()
    if call.from_user.id in ADMINS:
        questions = await db.all_questions()
        kb = await inline.create_edit_questions_kb(questions)
        await call.message.answer(
            'Ниже представлена информация в виде: номер опроса || текст вопроса. Можете менять вопросы и создавать новые',
            reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith('new_question'))
async def new_question_start(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Введите новый текст для вопроса в формате: номер опроса | текст вопроса')
    await state.set_state(Admins.new_question)


@router.callback_query(F.data.startswith('change_question'))
async def edit_question(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    survey_index = data[2]
    question_index = data[3]
    await call.message.answer(f'Введите новый текст для вопроса {question_index} из опроса {survey_index}')
    await state.update_data(question_index=question_index)
    await state.update_data(survey_index=survey_index)
    await state.set_state(Admins.edit_question)
@router.callback_query(F.data.startswith('admin_user_inspect'))
async def admin_user_find(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Введите ID пользователя")
    await state.set_state(Admins.edit_role)

@router.message(Admins.edit_role)
async def admin_inspect_user(message: types.Message, state: FSMContext):
    await state.clear()
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🛡️')]], resize_keyboard=True)
    try:
        if int(message.text) not in await db.get_all_users():
            await message.answer("Пользователь с таким ID не зарегистрирован в боте. Попробуйте еще раз или нажмите на кнопку",reply_markup=kb)
            return None
    except Exception as e:
        await message.answer("Неверный тип ввода. Попробуйте еще раз.", reply_markup=kb)
    user_id = int(message.text)
    user_data = await db.get_user_stats(user_id)
    text = f'''*Профиль пользователя {user_id}*\n
Пройдено опросов ✔️: {user_data['surveys_count']}\n
Пол: {'👨' if user_data['sex'] == 'Мужской' else '👩'}\n
Возраст: {user_data['age']}\n
Образование 🎓: {user_data['education']}\n'''
    if user_data['role'] == 'user':
        text += 'Роль: пользователь'
    elif user_data['role'] == 'admin':
        text += 'Роль: администратор проекта'
    elif user_data['role'] == 'survey_admin':
        text += 'Роль: администратор опросов'
    kb = await inline.user_inspect_kb(user_id)
    await message.answer(text, parse_mode=ParseMode.MARKDOWN,reply_markup=kb.as_markup())
    return None
@router.callback_query(F.data.startswith('user_edit_role'))
async def user_edit_role(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    user_id = call.data.split('_')[3]
    kb = await inline.user_role_edit_kb(int(user_id))
    await call.message.answer('Выберите роль',reply_markup=kb.as_markup())
@router.callback_query(F.data.startswith('user_commit_role'))
async def user_commit_role(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    user_id = call.data.split('_')[3]
    role = call.data.split('_')[4]
    if role == "adminsurvey":
        await db.change_user_stat(int(user_id), "role", "survey_admin")
    else:
        await db.change_user_stat(int(user_id), "role", role)
    await call.message.answer(f"Успешно изменена роль {user_id} на '{role}'")
    await admin_command(call.message,state)

@router.message(Admins.new_question)
async def new_question(message: types.Message, state: FSMContext):
    msg = message.text.split('|')
    survey_index = int(msg[0])
    quest_text = msg[1]
    quest_index = 1
    try:
        response = await api.get_questions(survey_index)
        if response['data']:
            quest_index = response['data'][-1]['question_index'] + 1

    except Exception as e:
        print(e)
    await db.create_client()
    await db.add_question(quest_index, survey_index, quest_text)
    await state.clear()
    await admin_command(message,state)


@router.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    await db.create_client()
    edited_question = message.text
    data = await state.get_data()
    await db.change_question(int(data['question_index']), int(data['survey_index']), edited_question)
    await message.answer('Успешно изменен вопрос')
    await admin_command(message,state)