from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import helpers.api as api
from bot.states import UserLLM
from helpers.student_result import get_student_result
from helpers.gad7_predict import form_gad7_survey_1, predict_stress_level
from bot.utils.messages import get_processing_message
from bot.utils.keyboards import build_back_button
from llm_service.interaction import get_final_recommendation

router = Router()


async def finish_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result = data.get('result', {})
    survey_n = data.get('survey_n', 1)
    user_id = data.get('user_id', 0)
    global_n = data.get('global_n')
    
    if not result:
        await message.answer(
            "❌ Не удалось обработать ответы.\n\nПопробуй ещё раз.",
            reply_markup=build_back_button()
        )
        await state.clear()
        return
    
    processing_msg = await message.answer(get_processing_message())
    
    try:
        sorted_keys = sorted(result.keys())
        if survey_n == 1:
            user_data = await api.get_user(user_id)
            sex = user_data['sex']
            education = user_data['education']
            age = user_data['age']
            form = await form_gad7_survey_1([result[i] for i in sorted_keys],sex,age,education)
            predicted_level = await predict_stress_level(form)
        if survey_n == 2:
            predicted_level = await get_student_result([result[i] for i in sorted_keys])

    except Exception as e:
        print(f"Error calculating result: {e}")
        predicted_level = -1
    
    try:
        await processing_msg.delete()
    except:
        pass
    
    if predicted_level == -1:
        await message.answer(
            "❌ Ошибка при обработке.\n\nПопробуй пройти опрос ещё раз.",
            reply_markup=build_back_button()
        )
    else:
        if predicted_level < 30:
            level_desc = "низкий"
            emoji = "🟢"
        elif predicted_level < 60:
            level_desc = "умеренный"
            emoji = "🟡"
        else:
            level_desc = "высокий"
            emoji = "🔴"
        recommendations = await get_final_recommendation(predicted_level)
        kb = build_back_button()
        if level_desc == "высокий":
            kb = build_back_button(help=1)
        await message.answer(
            f"📊 <b>Результаты анализа</b>\n\n"
            f"{emoji} Твой уровень тревожности: <b>{predicted_level}%</b>\n"
            f"Уровень: {level_desc}\n\n"
            f"Мои рекомендации для тебя: \n\n"
            f"{recommendations}\n"
            f"<i>Помни: этот результат — лишь повод прислушаться к себе, а не диагноз.</i>",
            parse_mode="HTML",
            reply_markup=kb
        )
        
        if global_n:
            await api.add_survey_result(
                user_id,
                global_n,
                survey_n,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                predicted_level
            )
    
    await state.clear()


async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions_list', [])
    question_n = data.get('question_n', 1)
    total = len(questions)
    
    if question_n > len(questions):
        await finish_test(message, state)
        return
    
    llm_resp = await api.rephrase_question(questions[question_n - 1])
    current_question = llm_resp['llm_response']
    progress_text = f"💬 <b>Вопрос {question_n}/{total}</b>"
    
    await message.answer(
        f"{progress_text}\n\n{current_question}",
        parse_mode="HTML"
    )



@router.callback_query(F.data.startswith("llm_choose_"))
async def llm_choose(call: CallbackQuery, state: FSMContext):
    call_data = call.data.split("_")[2]
    survey_n = 1 if call_data == 'gad7' else 2
    data = await api.get_questions(survey_n)
    if not data or 'data' not in data:
        await call.message.answer("❌ Ошибка загрузки вопросов. Попробуй позже.")
        return

    questions_list = [x['question_text'] for x in data['data']]
    global_n = data.get('global_n')
    question_n = 1
    result = {}
    await state.set_state(UserLLM.answer)
    await state.update_data(survey_n=survey_n)
    await state.update_data(questions_list=questions_list)
    await state.update_data(global_n=global_n)
    await state.update_data(question_n=question_n)
    await state.update_data(result=result)
    await state.update_data(attempt=0)
    await state.update_data(user_id=call.from_user.id)

    await ask_question(call.message, state)
@router.callback_query(F.data.startswith('start_llm_mode'))
async def llm_talk_start(call: types.CallbackQuery):
    await call.answer()
    await call.message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Про учебу',callback_data='llm_choose_study'))
    builder.row(InlineKeyboardButton(text='Про общее состояние',callback_data='llm_choose_gad7'))
    await call.message.answer(
        "💬 <b>Режим разговора</b>\n\n"
        "Я задам тебе несколько вопросов.\n\n"
        "Отвечай честно и развёрнуто — это поможет лучше понять твоё состояние."
        "На какую тему хочешь поговорить?",
        parse_mode="HTML", reply_markup=builder.as_markup()
    )


@router.message(UserLLM.answer)
async def llm_talk_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions_list', [])
    question_n = data.get('question_n', 1)
    result = data.get('result', {})
    attempt = data.get('attempt', 0)
    
    if question_n > len(questions):
        await finish_test(message, state)
        return
    
    user_answer = message.text
    current_question = questions[question_n - 1]
    
    processing_msg = await message.answer(get_processing_message())
    
    api_response = await api.generate_llm(
        current_question,
        question_n,
        user_answer,
        result,
        attempt
    )
    
    try:
        await processing_msg.delete()
    except:
        pass
    
    if not api_response or 'llm_response' not in api_response:
        await message.answer("❌ Ошибка обработки. Попробуй ответить ещё раз.")
        return
    
    llm_response = api_response['llm_response']
    if isinstance(llm_response, list) and llm_response[0] == -999:
        await message.answer(
            "🛑 <b>МЫ ОЧЕНЬ ЗА ТЕБЯ ПЕРЕЖИВАЕМ</b>\n\n"
            "Похоже, ты сейчас в критическом состоянии. Я всего лишь бот и не могу помочь по-настоящему, "
            "но есть люди, которые могут и хотят помочь прямо сейчас.\n\n"
            "📞 <b>8 (800) 200-01-22</b> — Федеральный телефон доверия (Анонимно)\n"
            "📞 <b>112</b> — Экстренная служба\n\n"
            "Пожалуйста, не оставайся с этим в одиночестве. Позвони.",
            parse_mode="HTML"
        )
        await state.clear()
        return


    if isinstance(llm_response, list) and len(llm_response) == 2 and llm_response[0] == -1:
        follow_up_question = llm_response[1]
        await state.update_data(attempt=attempt + 1)
        await message.answer(f"❓ {follow_up_question}")
        return
    
    if isinstance(llm_response, dict):
        result = llm_response
        question_n += 1
        await state.update_data(question_n=question_n)
        await state.update_data(result=result)
        await state.update_data(attempt=0)  
        await ask_question(message, state)
    else:
        await message.answer("❌ Ошибка обработки. Попробуй ответить ещё раз.")
