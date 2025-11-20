from datetime import datetime

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
import helpers.api as api
from bot.states import UserLLM
from llm_service.interaction import analyze_question
from helpers.student_result import get_student_result

router = Router()


async def finish_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result = data['result']
    global_n = data['global_n']
    await message.answer("Спасибо за разговор. Сейчас постараюсь определить твоей уровень тревожности.")
    predicted_level = await get_student_result([result[i] for i in result])
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🔙')]],resize_keyboard=True)
    await message.answer(f"Твой уровень тревожности: {predicted_level}%", reply_markup=kb)
    await api.add_survey_result(message.from_user.id,global_n,2,str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),predicted_level)







async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions_list']
    question_n = data['question_n']
    if question_n == len(questions)+1:
        await finish_test(message, state)
    else:
        await message.answer(text=questions[question_n-1])

@router.callback_query(F.data.startswith('start_llm_mode'))
async def llm_talk_start(call: types.CallbackQuery,state: FSMContext):
    await call.message.answer("Я задам тебе пару вопросов, постарайся ответить на них честно и развернуто")
    data = await api.get_questions(2)
    questions_list = [x['question_text'] for x in data['data']]
    global_n = data['global_n']
    question_n = 1
    result = {}
    await state.set_state(UserLLM.answer)
    await state.update_data(questions_list=questions_list)
    await state.update_data(global_n=global_n)
    await state.update_data(question_n=question_n)
    await state.update_data(result=result)
    await ask_question(call.message, state)

@router.message(UserLLM.answer)
async def llm_talk_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions_list']
    question_n = data['question_n']
    result = data['result']
    user_answer = message.text
    llm_response = await analyze_question(questions[question_n-1], question_n,user_answer, result)
    print("LLM: " + str(llm_response))
    if type(llm_response) is list and llm_response[0] == -1:
        await message.answer(llm_response[1])
        return
    else:
        result = llm_response
        question_n += 1
        await state.update_data(question_n=question_n)
        await state.update_data(result=result)
        await ask_question(message, state)

