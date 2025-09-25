from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def create_admin_commands():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Посмотреть список вопросов',callback_data='admin_show_questions'))
    return builder


async def create_edit_questions_kb(questions):
    builder = InlineKeyboardBuilder()
    for i in questions:
        builder.row(InlineKeyboardButton(text=i, callback_data=f'question_{questions.index(i)}'))
    builder.row(InlineKeyboardButton(text='Добавить новый вопрос',callback_data='question_create'))
    return builder