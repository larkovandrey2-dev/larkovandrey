import os
from datetime import datetime

from aiogram import Router, types, F
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
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

@router.message(Command('admin'))
async def admin_command(message: types.Message):
    if message.from_user.id in ADMINS:
        builder = await inline.create_admin_commands()
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
    if str(call.from_user.id) in ADMINS:
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
    await admin_command(message)


@router.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    await db.create_client()
    edited_question = message.text
    data = await state.get_data()
    await db.change_question(int(data['question_index']), int(data['survey_index']), edited_question)
    await message.answer('Успешно изменен вопрос')
    await admin_command(message)