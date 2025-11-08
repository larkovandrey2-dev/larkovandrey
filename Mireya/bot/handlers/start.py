import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import ADMINS
from bot.states import UserConfig
from bot.services.database import DatabaseService
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()

@router.message(F.text == "Назад 🔙")
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await db.create_client()
    await db.change_user_stat(message.from_user.id, "role", "admin")
    if message.from_user.id not in await db.get_all_users():
        await message.answer('Вы в нашем сервисе впервые. Введите свой возраст')
        await state.set_state(UserConfig.age)
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(types.InlineKeyboardButton(text='Пройти опрос', callback_data='start_test'))
        keyboard.row(types.InlineKeyboardButton(text='Поговорить', callback_data='start_llm_mode'))
        keyboard.row(types.InlineKeyboardButton(text='Личный кабинет', callback_data='personal_lk'))
        username = message.from_user.username
        if message.from_user.id not in ADMINS:
            text = f'''Добро пожаловать, @{username}, я Mireya. Здесь нет правильных или неправильных ответов - только твои ощущения. Сейчас мне важно лучше узнать, что ты чувствуешь, чтобы увидеть картину твоего душевного состояния. Для этого я предложу короткий опрос. Он очень простой, но с его помощью мы сможем вместе чуть яснее взглянуть на твои эмоции и настроение.'''
            await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        if message.from_user.id in ADMINS:
            text = f'''Добро пожаловать, администратор (/admin)'''
            await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await message.answer('Выберите действие: ', reply_markup=keyboard.as_markup())
@router.message(UserConfig.age)
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


@router.message(UserConfig.sex)
async def sex_setup(message: types.Message, state: FSMContext):
    sex = message.text.split()[0]
    await state.update_data(sex=sex)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await message.answer('Выберите уровень образования: ', reply_markup=kb)
    await state.set_state(UserConfig.education)


@router.message(UserConfig.education)
async def finish_setup(message: types.Message, state: FSMContext):
    await db.create_client()
    education = message.text
    data = await state.get_data()
    sex = data['sex'].split()[0]
    age = data['age']
    if education not in ['Высшее образование','Основное общее образование','Среднее общее']:
        await message.answer('Выберите корректный уровень образования: ')
    else:
        if str(message.from_user.id) in ADMINS:
            await db.create_user(message.from_user.id, 'admin', 0)
        else:
            await db.create_user(message.from_user.id, 'user', 0)
        await db.change_user_stat(message.from_user.id, 'education', education)
        await db.change_user_stat(message.from_user.id, 'sex', sex)
        await db.change_user_stat(message.from_user.id, 'age', int(age))
        await start(message, state)