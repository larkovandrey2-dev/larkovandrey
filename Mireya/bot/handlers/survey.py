import os
from datetime import datetime

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton

from bot.states import Questions
from bot.services.database import DatabaseService
import bot.services.api as api
from bot.utils import gad7_predict as gad7
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()

async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    print(question_list)
    current_question = [i['question_text'] for i in question_list if i['question_index'] == question_n][0]
    await message.answer(current_question)


async def finish_test(message: types.Message, state: FSMContext):
    await db.create_client()
    data = await state.get_data()
    survey_n = data['question_list'][0]['survey_index']
    user_data = await db.get_user_stats(message.from_user.id)
    global_n = data['global_n']
    surveys_user_c = user_data['surveys_count']
    results_list = user_data['all_user_global_attempts']
    if results_list is None:
        results_list = []
    results_list.append(global_n)
    if surveys_user_c is None:
        surveys_user_c = 0
    await db.change_user_stat(message.from_user.id, 'last_survey_index', survey_n)
    await db.change_user_stat(message.from_user.id, 'surveys_count', surveys_user_c + 1)
    await db.change_user_stat(message.from_user.id, 'all_user_global_attempts', results_list)
    await state.clear()
    await message.answer('Опрос заверешен. Твои ответы получены, и сейчас ты увидишь свой уровень стресса/тревожности')
    user_answers = await db.get_answers_by_global_attempt(int(global_n))
    user_answers.sort(key=lambda x: x['question_index'])
    user_answers = [i['response_text'] for i in user_answers]
    ans_form = await gad7.form_gad7_survey_1(user_answers, user_data['sex'], user_data['age'],
                                                user_data['education'])
    predicted_level = await gad7.predict_stress_level(ans_form)
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🔙')]],resize_keyboard=True)
    if predicted_level == -1:
        await message.answer("Ошибка в корректности введеных ответов. Пройдите тест еще раз и попытайтесь отвечать правильно")
    else:
        await message.answer(f'Предполагаемый уровень стресса/тревожности: {predicted_level}%', reply_markup=kb)
    await db.add_survey_result(message.from_user.id, global_n, survey_n,
                                             str(datetime.now().strftime('%Y-%M-%D %H:%M:%S')),
                                             predicted_level)


@router.callback_query(F.data.startswith("start_test"))
async def start_test(call: CallbackQuery, state: FSMContext):
    await db.create_client()
    await state.clear()
    data = await api.get_question_list(call.from_user.id)
    global_surveys_n = list(set(await db.all_global_attempts()))
    global_surveys_n.sort()
    if not global_surveys_n:
        global_surveys_n = [0]
    await state.update_data(question_list=data)
    await state.update_data(question_n=1)
    await state.update_data(global_n=global_surveys_n[-1] + 1)
    await state.set_state(Questions.questions)
    await ask_question(call.message, state)


@router.message(Questions.questions)
async def message_test(message: types.Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    global_n = data['global_n']
    survey_n = question_list[0]['survey_index']
    await api.add_answer(message.from_user.id,global_n,survey_n,question_n,text,str(datetime.now()))
    if question_n == len(question_list):
        await finish_test(message, state)
        return None
    question_n += 1
    await state.update_data(question_n=question_n)
    await ask_question(message, state)