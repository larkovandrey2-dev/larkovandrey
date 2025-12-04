import os

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, CallbackQuery

from bot.config import ADMINS
from bot.states import Admins
from helpers.database import DatabaseService
from bot.utils.kbs import inline
import helpers.api as api

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()
@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    
    user_data = await api.get_user(call.from_user.id)
    if not user_data:
        await call.message.answer('❌ Ошибка загрузки данных пользователя.')
        return
    
    user_role = user_data.get('role', 'user')
    if "admin" in user_role:
        builder = await inline.create_admin_commands(user_role)
        await call.message.answer(
            '🛡️ <b>Админ-панель</b>\n\nВыбери действие:',
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await call.answer('❌ Доступ запрещён.', show_alert=True)


@router.message(F.text == 'Назад 🛡️')
@router.message(Command('admin'))
async def admin_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_data = await api.get_user(message.from_user.id)
    if not user_data:
        await message.answer('❌ Ошибка загрузки данных пользователя.')
        return
    
    user_role = user_data.get('role', 'user')
    if "admin" in user_role:
        builder = await inline.create_admin_commands(user_role)
        await message.answer(
            '🛡️ <b>Админ-панель</b>\n\nВыбери действие:',
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer('❌ Доступ запрещён.')


@router.callback_query(F.data.startswith('admin_delete_questions'))
async def admin_delete_questions_list(call: CallbackQuery):
    await call.answer()
    data = await api.get_all_questions()
    if not data:
        await call.message.answer("Ошибка загрузки вопросов.")
        return
    questions = data.get('questions') or data.get('data', [])
    if not questions:
        await call.message.answer("Вопросы не найдены.")
        return
    kb = await inline.create_deletion_question_list(questions)
    await call.message.answer('Выберите вопрос для удаления:', reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith('delete_question'))
async def delete_question(call: CallbackQuery):
    await call.answer()
    data = call.data.split('_')
    survey_index = int(data[2])
    question_index = int(data[3])
    
    await api.delete_question(question_index, survey_index)
    response = await api.get_questions(survey_index)
    
    if response and response.get('data'):
        questions = response['data']
        if questions:
            first_question_index = int(questions[0]['question_index'])
            for i in range(1, len(questions)):
                await db.change_question_index(
                    int(questions[i]['question_index']),
                    int(questions[i]['survey_index']),
                    first_question_index + i
                )
    
    await call.message.answer('✅ Вопрос удалён')
    await admin_delete_questions_list(call)


@router.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    await call.answer()
    if call.from_user.id in ADMINS:
        data = await api.get_all_questions()
        if not data:
            await call.message.answer("Ошибка загрузки вопросов.")
            return
        questions = data.get('questions') or data.get('data', [])
        if not questions:
            await call.message.answer("Вопросы не найдены.")
            return
        kb = await inline.create_edit_questions_kb(questions)
        await call.message.answer(
            'Список вопросов (номер опроса || текст вопроса):',
            reply_markup=kb.as_markup()
        )


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
        user_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введи число.", reply_markup=kb)
        return
    
    try:
        data = await api.get_all_users()
        if not data:
            await message.answer("Ошибка загрузки списка пользователей.", reply_markup=kb)
            return
        
        users_list = data if isinstance(data, list) else data.get('users', [])
        if user_id not in users_list:
            await message.answer("❌ Пользователь с таким ID не найден.", reply_markup=kb)
            return
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=kb)
        return
    
    user_data = await api.get_user(user_id)
    if not user_data:
        await message.answer("Ошибка загрузки данных пользователя.", reply_markup=kb)
        return
    
    sex_emoji = '👨' if user_data.get('sex') == 'Мужской' else '👩'
    role_text = {
        'user': 'пользователь',
        'admin': 'администратор проекта',
        'survey_admin': 'администратор опросов'
    }.get(user_data.get('role', 'user'), 'неизвестно')
    
    text = (
        f"*Профиль пользователя {user_id}*\n\n"
        f"Пройдено опросов: {user_data.get('surveys_count', 0)}\n"
        f"{sex_emoji} Пол: {user_data.get('sex', 'Не указан')}\n"
        f"Возраст: {user_data.get('age', 'Не указан')}\n"
        f"Образование: {user_data.get('education', 'Не указано')}\n\n"
        f"Роль: {role_text}"
    )
    
    kb = await inline.user_inspect_kb(user_id)
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb.as_markup())
@router.callback_query(F.data.startswith('user_edit_role'))
async def user_edit_role(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    user_id = call.data.split('_')[3]
    kb = await inline.user_role_edit_kb(int(user_id))
    await call.message.answer('Выберите роль',reply_markup=kb.as_markup())
@router.callback_query(F.data.startswith('user_commit_role'))
async def user_commit_role(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    data_parts = call.data.split('_')
    user_id = int(data_parts[3])
    role = data_parts[4]
    
    if role == "adminsurvey":
        await db.change_user_stat(user_id, "role", "survey_admin")
        role_display = "администратор опросов"
    else:
        await db.change_user_stat(user_id, "role", role)
        role_display = role
    
    await call.message.answer(f"✅ Роль пользователя {user_id} изменена на '{role_display}'")
    await admin_command(call.message, state)

@router.message(Admins.new_question)
async def new_question(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split('|')
        if len(parts) < 2:
            await message.answer("❌ Неверный формат. Используй: номер опроса | текст вопроса")
            return
        
        survey_index = int(parts[0].strip())
        quest_text = parts[1].strip()
        quest_index = 1
        
        try:
            response = await api.get_questions(survey_index)
            if response and response.get('data'):
                quest_index = response['data'][-1]['question_index'] + 1
        except Exception as e:
            print(f"Error getting questions: {e}")
        
        await db.create_client()
        await db.add_question(quest_index, survey_index, quest_text)
        await state.clear()
        await message.answer(f"✅ Вопрос добавлен в опрос {survey_index}")
        await admin_command(message, state)
    except (ValueError, IndexError) as e:
        await message.answer("❌ Ошибка формата. Используй: номер опроса | текст вопроса")


@router.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    await db.create_client()
    edited_question = message.text.strip()
    data = await state.get_data()
    
    question_index = int(data.get('question_index', 0))
    survey_index = int(data.get('survey_index', 0))
    
    if not edited_question:
        await message.answer("❌ Текст вопроса не может быть пустым.")
        return
    
    await db.change_question(question_index, survey_index, edited_question)
    await message.answer('✅ Вопрос успешно изменён')
    await state.clear()
    await admin_command(message, state)