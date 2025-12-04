from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def create_admin_commands(role):
    """Create modern admin command menu."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='📋 Список вопросов',
        callback_data='admin_show_questions'
    ))
    builder.row(InlineKeyboardButton(
        text='🗑️ Удалить вопрос',
        callback_data='admin_delete_questions'
    ))
    if role == 'admin':
        builder.row(InlineKeyboardButton(
            text="👤 Информация о пользователе",
            callback_data="admin_user_inspect"
        ))
    return builder


async def create_deletion_question_list(questions: dict):
    """Create question deletion list with modern layout."""
    builder = InlineKeyboardBuilder()
    for i in questions:
        # Truncate long questions
        question_text = i['question_text']
        if len(question_text) > 40:
            question_text = question_text[:37] + "..."
        
        builder.row(InlineKeyboardButton(
            text=f"🗑️ Опрос {i['survey_index']}: {question_text}",
            callback_data=f"delete_question_{i['survey_index']}_{i['question_index']}"
        ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_menu"
    ))
    return builder


async def create_edit_questions_kb(questions: dict):
    """Create question editing keyboard."""
    builder = InlineKeyboardBuilder()
    for i in questions:
        # Truncate long questions
        question_text = i['question_text']
        if len(question_text) > 35:
            question_text = question_text[:32] + "..."
        
        builder.row(InlineKeyboardButton(
            text=f"✏️ Опрос {i['survey_index']}: {question_text}",
            callback_data=f'change_question_{i["survey_index"]}_{i["question_index"]}'
        ))
    builder.row(InlineKeyboardButton(
        text='➕ Добавить новый вопрос',
        callback_data='new_question'
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_menu"
    ))
    return builder


async def user_inspect_kb(user_id: int):
    """Create user inspection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить роль",
        callback_data=f"user_edit_role_{user_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_menu"
    ))
    return builder


async def user_role_edit_kb(user_id: int):
    """Create role editing keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="👤 Пользователь",
        callback_data=f"user_commit_role_{user_id}_user"
    ))
    builder.row(InlineKeyboardButton(
        text="👨‍💼 Администратор проекта",
        callback_data=f"user_commit_role_{user_id}_admin"
    ))
    builder.row(InlineKeyboardButton(
        text="📊 Администратор опросов",
        callback_data=f"user_commit_role_{user_id}_adminsurvey"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"admin_user_inspect"
    ))
    return builder
