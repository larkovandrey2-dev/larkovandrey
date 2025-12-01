import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.config import ADMINS
from bot.states import UserConfig
from helpers.database import DatabaseService
from bot.utils.keyboards import build_main_menu

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()


@router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await db.create_client()
    
    user_id = call.from_user.id
    username = call.from_user.username or "друг"
    
    if user_id not in await db.get_all_users():
        await call.message.answer(
            f"Привет, {username}! 👋\n\n"
            "Я <b>Mireya</b> — твой помощник в отслеживании эмоционального состояния.\n\n"
            "Для начала мне нужно узнать немного о тебе.\n\n"
            "🎂 <b>Сколько тебе лет?</b>",
            parse_mode="HTML"
        )
        await state.set_state(UserConfig.age)
    else:
        if user_id in ADMINS:
            text = (
                f"Добро пожаловать, администратор! 👨‍💼\n\n"
                f"Используй /admin для управления системой."
            )
        else:
            text = (
                f"Привет, {username}! 👋\n\n"
                f"Здесь нет правильных или неправильных ответов — только твои ощущения.\n\n"
                f"Я помогу тебе лучше понять своё эмоциональное состояние."
            )
        
        await call.message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await call.message.answer(
            "Выбери действие:",
            reply_markup=build_main_menu()
        )


@router.message(F.text == "Назад 🔙")
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await db.create_client()
    
    user_id = message.from_user.id
    username = message.from_user.username or "друг"
    
    if user_id not in await db.get_all_users():
        await message.answer(
            f"Привет, {username}! 👋\n\n"
            "Я <b>Mireya</b> — твой помощник в отслеживании эмоционального состояния.\n\n"
            "Для начала мне нужно узнать немного о тебе.\n\n"
            "🎂 <b>Сколько тебе лет?</b>",
            parse_mode="HTML"
        )
        await state.set_state(UserConfig.age)
    else:
        if user_id in ADMINS:
            text = (
                f"Добро пожаловать, администратор! 👨‍💼\n\n"
                f"Используй /admin для управления системой."
            )
        else:
            text = (
                f"Привет, {username}! 👋\n\n"
                f"Здесь нет правильных или неправильных ответов — только твои ощущения.\n\n"
                f"Я помогу тебе лучше понять своё эмоциональное состояние."
            )
        
        await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await message.answer(
            "Выбери действие:",
            reply_markup=build_main_menu()
        )


@router.message(UserConfig.age)
async def age_setup(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if not (14 < age < 100):
            await message.answer('❌ Пожалуйста, введи корректный возраст (от 15 до 99 лет)')
            return
    except ValueError:
        await message.answer('❌ Пожалуйста, введи число')
        return
    
    await state.update_data(age=age)
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='👨 Мужской')],
            [KeyboardButton(text='👩 Женский')]
        ]
    )
    await message.answer('👤 <b>Выбери пол:</b>', parse_mode="HTML", reply_markup=kb)
    await state.set_state(UserConfig.sex)


@router.message(UserConfig.sex)
async def sex_setup(message: types.Message, state: FSMContext):
    sex_text = message.text
    if 'Мужской' in sex_text or '👨' in sex_text:
        sex = 'Мужской'
    elif 'Женский' in sex_text or '👩' in sex_text:
        sex = 'Женский'
    else:
        await message.answer('❌ Пожалуйста, выбери пол из предложенных вариантов')
        return
    
    await state.update_data(sex=sex)
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='🎓 Высшее образование')],
            [KeyboardButton(text='📚 Основное общее образование')],
            [KeyboardButton(text='📖 Среднее общее')]
        ]
    )
    await message.answer('🎓 <b>Выбери уровень образования:</b>', parse_mode="HTML", reply_markup=kb)
    await state.set_state(UserConfig.education)


@router.message(UserConfig.education)
async def finish_setup(message: types.Message, state: FSMContext):
    education = message.text
    education_clean = education.replace('🎓', '').replace('📚', '').replace('📖', '').strip()
    
    valid_education = {
        'Высшее образование': 'Высшее образование',
        'Основное общее образование': 'Основное общее образование',
        'Среднее общее': 'Среднее общее'
    }
    
    matched_education = None
    for key, value in valid_education.items():
        if key in education_clean:
            matched_education = value
            break
    
    if not matched_education:
        await message.answer('❌ Пожалуйста, выбери уровень образования из предложенных вариантов')
        return
    
    await db.create_client()
    data = await state.get_data()
    sex = data['sex']
    age = data['age']
    user_id = message.from_user.id
    
    role = 'admin' if user_id in ADMINS else 'user'
    await db.create_user(user_id, role, 0)
    await db.change_user_stat(user_id, 'education', matched_education)
    await db.change_user_stat(user_id, 'sex', sex)
    await db.change_user_stat(user_id, 'age', age)
    
    await message.answer(
        '✅ Отлично! Настройка завершена.\n\nТеперь ты можешь начать работу с ботом.',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await start(message, state)
