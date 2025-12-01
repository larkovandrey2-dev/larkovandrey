import random
from typing import List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_gad7_buttons(current: int, total: int, question_n: int = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if question_n in [8, 9]:
        builder.row(
            InlineKeyboardButton(text="0", callback_data=f"gad7_answer_{current}_0"),
            InlineKeyboardButton(text="1", callback_data=f"gad7_answer_{current}_1"),
            InlineKeyboardButton(text="2", callback_data=f"gad7_answer_{current}_2"),
            InlineKeyboardButton(text="3", callback_data=f"gad7_answer_{current}_3"),
            InlineKeyboardButton(text="4", callback_data=f"gad7_answer_{current}_4"),
        )
    elif question_n == 10:
        builder.row(
            InlineKeyboardButton(text="0", callback_data=f"gad7_answer_{current}_0"),
            InlineKeyboardButton(text="1", callback_data=f"gad7_answer_{current}_1"),
            InlineKeyboardButton(text="2", callback_data=f"gad7_answer_{current}_2"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="0", callback_data=f"gad7_answer_{current}_0"),
            InlineKeyboardButton(text="1", callback_data=f"gad7_answer_{current}_1"),
            InlineKeyboardButton(text="2", callback_data=f"gad7_answer_{current}_2"),
            InlineKeyboardButton(text="3", callback_data=f"gad7_answer_{current}_3"),
        )
    
    return builder.as_markup()


def build_yes_no_buttons(current: int, total: int, prefix: str = "student") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌ Нет", callback_data=f"{prefix}_answer_{current}_0"),
        InlineKeyboardButton(text="🤔 Скорее нет", callback_data=f"{prefix}_answer_{current}_1"),
    )
    builder.row(
        InlineKeyboardButton(text="🤷 Скорее да", callback_data=f"{prefix}_answer_{current}_2"),
        InlineKeyboardButton(text="✅ Да", callback_data=f"{prefix}_answer_{current}_3"),
    )
    
    builder.row(
        InlineKeyboardButton(text=f"📊 Прогресс: {current}/{total}", callback_data="progress_info")
    )
    
    return builder.as_markup()


def build_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Пройти опрос", callback_data="start_test")
    )
    builder.row(
        InlineKeyboardButton(text="💬 Поговорить", callback_data="start_llm_mode")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="personal_lk")
    )
    builder.row(
        InlineKeyboardButton(text="💚 Поддержка", callback_data="psycho_info")
    )
    
    return builder.as_markup()


def build_survey_type_selector() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Общий опрос (GAD-7)", callback_data="start_common_test")
    )
    builder.row(
        InlineKeyboardButton(text="🎓 Для студентов", callback_data="start_student_test")
    )
    
    return builder.as_markup()


def build_profile_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✏️ Возраст", callback_data="lk_change_age"),
        InlineKeyboardButton(text="✏️ Пол", callback_data="lk_change_sex"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Образование", callback_data="lk_change_education")
    )
    builder.row(
        InlineKeyboardButton(text="📈 График тревожности", callback_data="lk_chart_chose")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def build_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data))
    return builder.as_markup()


def build_chart_selector(survey_indices: List[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    print(survey_indices)
    for idx in survey_indices:
        builder.row(
            InlineKeyboardButton(
                text=f"📊 Опрос {idx}",
                callback_data=f"lk_anxiety_chart_{idx}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="personal_lk")
    )
    
    return builder.as_markup()
