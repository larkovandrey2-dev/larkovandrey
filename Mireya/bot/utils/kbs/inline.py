from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def create_admin_commands(role):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Посмотреть список вопросов',callback_data='admin_show_questions'))
    builder.row(InlineKeyboardButton(text='Удалить вопрос',callback_data='admin_delete_questions'))
    if role == 'admin':
        builder.row(InlineKeyboardButton(text="Информация о пользователе",callback_data="admin_user_inspect"))
    return builder

async def create_deletion_question_list(questions: dict):
    builder = InlineKeyboardBuilder()
    for i in questions:
        builder.row(InlineKeyboardButton(text=f"{i['survey_index']} || {i['question_text']}", callback_data=f"delete_question_{i['survey_index']}_{i['question_index']}"))
    return builder
async def create_edit_questions_kb(questions:dict):
    builder = InlineKeyboardBuilder()
    for i in questions:
        builder.row(InlineKeyboardButton(text=f"{i['survey_index']} || {i['question_text']}", callback_data=f'change_question_{i["survey_index"]}_{i["question_index"]}'))
    builder.row(InlineKeyboardButton(text='Добавить новый вопрос',callback_data='new_question'))
    return builder

async def user_inspect_kb(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Изменить роль",callback_data=f"user_edit_role_{user_id}"))
    return builder
async def user_role_edit_kb(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пользователь",callback_data=f"user_commit_role_{user_id}_user"))
    builder.row(InlineKeyboardButton(text="Администратор проекта",callback_data=f"user_commit_role_{user_id}_admin"))
    builder.row(InlineKeyboardButton(text="Администратор опросов",callback_data=f"user_commit_role_{user_id}_adminsurvey"))
    return builder