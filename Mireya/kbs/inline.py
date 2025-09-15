from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def create_edit_questions_kb(questions):
    builder = InlineKeyboardBuilder()
    for i in questions:
        builder.row(InlineKeyboardButton(text=i, callback_data=f'question_{questions.index(i)}'))
    return builder