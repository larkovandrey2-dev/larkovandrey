import os
from datetime import datetime

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import Questions
from helpers.database import DatabaseService
import helpers.api as api
from helpers import gad7_predict as gad7, student_result as st_res

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()

async def ask_question(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    current_question = [i['question_text'] for i in question_list if i['question_index'] == question_n][0]
    if str(current_state) == "Questions:questions1":
        await message.answer(current_question)
    if str(current_state) == "Questions:questions2":
        kb = ReplyKeyboardMarkup(resize_keyboard=True,keyboard=[[KeyboardButton(text="Нет")],[KeyboardButton(text="Скорее нет, чем да")],[KeyboardButton(text="Скорее да, чем нет")],[KeyboardButton(text="Да")]])
        await message.answer(current_question, reply_markup=kb)



async def finish_test(message: types.Message, state: FSMContext):
    await db.create_client()
    data = await state.get_data()
    survey_n = data['question_list'][0]['survey_index']
    user_data = await db.get_user_stats(message.from_user.id)
    global_n = data['global_n']
    await state.clear()
    await message.answer('Опрос заверешен. Твои ответы получены, и сейчас ты увидишь свой уровень стресса/тревожности')
    user_answers = await db.get_answers_by_global_attempt(int(global_n))
    user_answers.sort(key=lambda x: x['question_index'])
    user_answers = [i['response_text'] for i in user_answers]
    predicted_level = -1
    if survey_n == 1:
        ans_form = await gad7.form_gad7_survey_1(user_answers, user_data['sex'], user_data['age'],
                                                    user_data['education'])
        predicted_level = await gad7.predict_stress_level(ans_form)
    if survey_n == 2:
        predicted_level = await st_res.get_student_result(user_answers)
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🔙')]],resize_keyboard=True)
    if predicted_level == -1:
        await message.answer("Ошибка в корректности введеных ответов. Пройдите тест еще раз и попытайтесь отвечать правильно",reply_markup=kb)
    else:
        await message.answer(f'Предполагаемый уровень стресса/тревожности: {predicted_level}%', reply_markup=kb)
        await api.add_survey_result(message.from_user.id, global_n, survey_n,
                                             str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                             predicted_level)


@router.callback_query(F.data.startswith("start_test"))
async def choose_test_type(callback_query: types.CallbackQuery, state: FSMContext):
    await db.create_client()
    await callback_query.message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Общий опрос",callback_data="start_common_test"))
    builder.row(InlineKeyboardButton(text="Опрос для студентов",callback_data="start_student_test"))
    await callback_query.message.answer("Выберите тип опроса: ",reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("start_common_test"))
async def start_common_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await db.change_user_stat(callback_query.from_user.id, 'last_survey_index', 2)
    await start_test(callback_query, state)
@router.callback_query(F.data.startswith("start_student_test"))
async def start_common_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await db.change_user_stat(callback_query.from_user.id, 'last_survey_index', 1)
    await start_test(callback_query, state)





async def start_test(call: CallbackQuery, state: FSMContext):
    await db.create_client()
    await state.clear()
    data = await api.get_question_list(call.from_user.id)
    question_list = data['questions']
    global_n = data["global_n"]
    survey_n = question_list[0]['survey_index']


    await state.update_data(question_list=question_list)
    await state.update_data(question_n=1)
    await state.update_data(global_n=global_n)
    if survey_n == 1:
        await state.set_state(Questions.questions1)
    if survey_n == 2:
        await state.set_state(Questions.questions2)
    await ask_question(call.message, state)



@router.message(Questions.questions2)
async def student_test_message(message: types.Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    global_n = data['global_n']
    survey_n = question_list[0]['survey_index']
    if text not in ["Нет","Скорее нет, чем да", "Скорее да, чем нет", "Да"]:
        await message.answer("Выберите корректный ответ из предложенных")
        return None
    else:
        await api.add_answer(message.from_user.id, global_n, survey_n, question_n, text, str(datetime.now()))
        if question_n == len(question_list):
            await finish_test(message, state)
            return None
        question_n += 1
        await state.update_data(question_n=question_n)
        await ask_question(message, state)



@router.message(Questions.questions1)
async def message_test(message: types.Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    global_n = data['global_n']
    survey_n = question_list[0]['survey_index']
    try:
        if question_n != len(question_list):
            int(text)
            if question_n in [1,2,3,4,5,6,7] and (3 < int(text) or int(text) < 0) :
                raise ValueError
            elif question_n in [8,9] and (4 < int(text) or int(text) < 0):
                raise ValueError
            elif question_n == 10 and (2 < int(text) or int(text) < 0):
                raise ValueError
    except Exception as e:
        await message.answer("Вводите корректный ответ: в заданных рамках и нужного формата")
        return None
    await api.add_answer(message.from_user.id, global_n, survey_n, question_n, text, str(datetime.now()))
    if question_n == len(question_list):
        await finish_test(message, state)
        return None
    question_n += 1
    await state.update_data(question_n=question_n)
    await ask_question(message, state)