import os
from aiogram import Router, types, F
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import UserChanges
from bot.config import API_URL
from bot.services.database import DatabaseService
from aiogram.types import BufferedInputFile

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()

@router.callback_query(F.data.startswith('personal_lk'))
async def personal_lk(call: CallbackQuery):
    await db.create_client()
    req = f"{API_URL}/get_user/{call.from_user.id}"

    async with aiohttp.ClientSession() as session:
        data = await session.get(req)
        data = await data.json()
    print(data["all_user_global_attempts"])
    text = f'''#Профиль пользователя @{call.from_user.username}#\n
🆔: {call.message.from_user.id}\n
Пройдено опросов ✔️: {data['surveys_count']}\n
Пол: {'👨' if data['sex'] == 'Мужской' else '👩'}\n
Возраст: {data['age']}\n
Образование 🎓: {data['education']}\n\n'''
    if data['role'] == 'user':
        text += 'Ваша роль: пользователь'
    elif data['role'] == 'admin':
        text += 'Ваша роль: администратор'
    elif data['role'] == 'psychologist':
        text += 'Ваша роль: психолог'
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Изменить возраст",callback_data="lk_change_age"))
    builder.row(InlineKeyboardButton(text="Изменить пол",callback_data="lk_change_sex"))
    builder.row(InlineKeyboardButton(text="Изменить образование",callback_data="lk_change_education"))
    builder.row(InlineKeyboardButton(text="График твоей тревожности",callback_data="lk_chart_chose"))
    await call.message.answer(text,parse_mode=ParseMode.MARKDOWN,reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith('lk_chart_chose'))
async def choose_lk_chart(call: CallbackQuery):
    await call.message.delete()
    data = await db.get_surveys_results(call.from_user.id)
    surveys_n = set([data[i]["survey_index"] for i in range(len(data))])
    builder = InlineKeyboardBuilder()
    for i in range(1,len(surveys_n)+1):
        builder.row(InlineKeyboardButton(text=f'Опрос {i}',callback_data=f'lk_anxiety_chart_{i}'))
    await call.message.answer('Выберите опрос, по которому хотите увидеть график своей тревожности',reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith('lk_anxiety_chart_'))
async def lk_anxiety_chart(call: CallbackQuery):
    survey_n = call.data.split('_')[3]
    img_buffer = await db.create_results_chart(call.from_user.id, int(survey_n))  # user_id: 10, survey_index: 1
    if img_buffer:
        input_file = BufferedInputFile(
            file=img_buffer.getvalue(),
            filename=f"stress_chart.png"
        )
        await call.message.answer_photo(
            photo=input_file,
            caption="Ваша динамика уровня стресса"
        )
        img_buffer.close()


@router.callback_query(F.data.startswith('lk_change_sex'))
async def lk_change_sex(call: CallbackQuery):
    user_data = await db.get_user_stats(call.from_user.id)
    sex = user_data['sex']
    if sex == 'Мужской':
        await db.change_user_stat(int(call.from_user.id), 'sex','Женский')
    else:
        await db.change_user_stat(int(call.from_user.id), 'sex', 'Мужской')
    await call.message.delete()
    await personal_lk(call)
@router.callback_query(F.data.startswith('lk_change_age'))
async def lk_change_age(call: CallbackQuery,state: FSMContext):
    await call.message.delete()
    user_data = await db.get_user_stats(call.from_user.id)
    await call.message.answer("Введите свой возраст: ")
    await state.set_state(UserChanges.age)
    await state.update_data(callback=call)
@router.message(UserChanges.age)
async def lk_change_age_commit(message: types.Message,state: FSMContext):
    age = message.text
    data = await state.get_data()
    if not age.isdecimal() or not(16 < int(age) < 100):
        await message.answer('Введите корректный возраст: ')
    else:
        await db.change_user_stat(message.from_user.id, 'age', int(age))
        await personal_lk(data['callback'])
        await state.clear()
@router.callback_query(F.data.startswith('lk_change_education'))
async def lk_change_education(call: CallbackQuery,state: FSMContext):
    user_data = await db.get_user_stats(call.from_user.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await call.message.delete()
    await call.message.answer('Выберите уровень образования: ',reply_markup=kb)
    await state.set_state(UserChanges.education)
    await state.update_data(callback=call)
@router.message(UserChanges.education)
async def lk_change_education_commit(message: types.Message,state: FSMContext):
    education = message.text
    data = await state.get_data()
    if education not in ['Высшее образование','Основное общее образование','Среднее общее']:
        await message.answer('Выберите корректный уровень образования: ')
    else:
        await db.change_user_stat(message.from_user.id, 'education', education)
        await message.answer('Изменение успешно!',reply_markup=types.ReplyKeyboardRemove())
        await personal_lk(data['callback'])
        await state.clear()