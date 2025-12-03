import os
from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import Questions
from helpers.database import DatabaseService
import helpers.api as api
from helpers import gad7_predict as gad7, student_result as st_res
from bot.utils.keyboards import (
    build_gad7_buttons,
    build_yes_no_buttons,
    build_survey_type_selector,
    build_back_button
)
from bot.utils.messages import get_contextual_comment, get_progress_emoji
from llm_service.interaction import get_final_recommendation

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()


async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    total = len(question_list)
    
    current_question = next(
        (q['question_text'] for q in question_list if q['question_index'] == question_n),
        None
    )
    
    if not current_question:
        await finish_test(message, state)
        return
    
    current_state = await state.get_state()
    progress_emoji = get_progress_emoji(question_n, total)
    
    if current_state == Questions.questions1:
        progress_text = f"{progress_emoji} <b>Вопрос {question_n}/{total}</b>"
        
        if question_n == 11:
            question_text = (
                f"{progress_text}\n\n❓ {current_question}\n\n"
                f"<i>Введи название игры текстом (например: League of Legends, Counter Strike и т.д.)</i>"
            )
            await message.answer(question_text, parse_mode="HTML")
        else:
            question_text = f"{progress_text}\n\n❓ {current_question}\n\n<i>Выбери ответ:</i>"
            await message.answer(
                question_text,
                parse_mode="HTML",
                reply_markup=build_gad7_buttons(question_n, total, question_n)
            )
    
    elif current_state == Questions.questions2:
        progress_text = f"{progress_emoji} <b>Вопрос {question_n}/{total}</b>"
        question_text = f"{progress_text}\n\n❓ {current_question}"
        
        await message.answer(
            question_text,
            parse_mode="HTML",
            reply_markup=build_yes_no_buttons(question_n, total, "student")
        )


async def finish_test(message: types.Message, state: FSMContext, user_id = None):
    await db.create_client()
    data = await state.get_data()
    question_list = data.get('question_list', [])
    
    if not question_list:
        await message.answer("❌ Ошибка: данные опроса не найдены.")
        await state.clear()
        return
    
    survey_n = question_list[0]['survey_index']
    if user_id is None:
        user_data = await db.get_user_stats(message.from_user.id)
    else:
        user_data = await db.get_user_stats(user_id)
    global_n = data['global_n']
    
    await state.clear()
    
    processing_msg = await message.answer("💭 Обрабатываю результаты...")
    
    user_answers = await db.get_answers_by_global_attempt(int(global_n))
    user_answers.sort(key=lambda x: x['question_index'])
    user_answers = [item['response_text'] for item in user_answers]
    
    predicted_level = -1
    try:
        if survey_n == 1:
            while len(user_answers) < 11:
                user_answers.append("0")
            
            ans_form = await gad7.form_gad7_survey_1(
                user_answers,
                user_data.get('sex', 'Мужской'),
                user_data.get('age', 20),
                user_data.get('education', 'Среднее общее')
            )
            if ans_form:
                predicted_level = await gad7.predict_stress_level(ans_form)
        elif survey_n == 2:
            predicted_level = await st_res.get_student_result(user_answers)
    except Exception as e:
        print(f"Error calculating result: {e}")
        import traceback
        traceback.print_exc()

    try:
        await processing_msg.delete()
    except:
        pass
    
    if predicted_level == -1:
        await message.answer(
            "❌ Ошибка при обработке ответов.\n\n"
            "Пожалуйста, пройди опрос ещё раз.",
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
        await message.answer(
            f"📊 <b>Результаты анализа</b>\n\n"
            f"{emoji} Твой уровень тревожности: <b>{predicted_level}%</b>\n"
            f"Уровень: {level_desc}\n\n"
            f"Мои рекомендации для тебя: \n\n"
            f"{recommendations}\n"
            f"<i>Помни: этот результат — лишь повод прислушаться к себе, а не диагноз.</i>",
            parse_mode="HTML",
            reply_markup=build_back_button()
        )
        if user_id is None:
            await api.add_survey_result(
                user_id=message.from_user.id,
                global_n=global_n,
                survey_n=survey_n,
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                result=predicted_level
            )
        else:
            await api.add_survey_result(
                user_id=user_id,
                global_n=global_n,
                survey_n=survey_n,
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                result=predicted_level
            )


@router.callback_query(F.data.startswith("start_test"))
async def choose_test_type(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.delete()
    
    await callback_query.message.answer(
        "📋 <b>Выбери тип опроса:</b>",
        parse_mode="HTML",
        reply_markup=build_survey_type_selector()
    )


@router.callback_query(F.data.startswith("start_common_test"))
async def start_common_test(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Начинаем общий опрос...")
    await callback_query.message.delete()
    await db.change_user_stat(callback_query.from_user.id, 'last_survey_index', 2)
    await start_test(callback_query, state)


@router.callback_query(F.data.startswith("start_student_test"))
async def start_student_test(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Начинаем опрос для студентов...")
    await callback_query.message.delete()
    await db.change_user_stat(callback_query.from_user.id, 'last_survey_index', 1)
    await start_test(callback_query, state)


async def start_test(call: CallbackQuery, state: FSMContext):
    await db.create_client()
    await state.clear()

    data = await api.get_question_list(call.from_user.id)
    if not data or 'questions' not in data:
        await call.message.answer("❌ Ошибка загрузки вопросов. Попробуй позже.")
        return

    question_list = data['questions']

    if not question_list:
        await call.message.answer("❌ Вопросы не найдены.")
        return

    survey_n = question_list[0]['survey_index']

    global_n = await db.get_next_global_number()

    await state.update_data(
        question_list=question_list,
        question_n=1,
        survey_n=survey_n,
        global_n=global_n
    )

    if survey_n == 1:
        await state.set_state(Questions.questions1)
        await call.message.answer(
            "📋 <b>Общий опрос (GAD-7)</b>\n\n"
            "Отвечай на вопросы честно.\n"
            "Нет правильных или неправильных ответов — только твои ощущения.\n\n"
            "<i>Вопросы 1-7: выбери число от 0 до 3\n"
            "Вопросы 8-9: выбери число от 0 до 4\n"
            "Вопрос 10: выбери число от 0 до 2\n"
            "Вопрос 11: введи название игры текстом</i>",
            parse_mode="HTML"
        )
    elif survey_n == 2:
        await state.set_state(Questions.questions2)
        await call.message.answer(
            "🎓 <b>Опрос для студентов</b>\n\n"
            "Выбирай ответ из предложенных вариантов.",
            parse_mode="HTML"
        )

    await ask_question(call.message, state)


@router.callback_query(F.data.startswith("gad7_answer_"))
async def handle_gad7_answer(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    parts = call.data.split("_")
    if len(parts) < 4:
        await call.answer("❌ Ошибка формата данных", show_alert=True)
        return
    
    try:
        question_n = int(parts[2])
        answer = int(parts[3])
        
        if question_n in [8, 9]:
            if not (0 <= answer <= 4):
                await call.answer("❌ Ответ должен быть от 0 до 4", show_alert=True)
                return
        elif question_n == 10:
            if not (0 <= answer <= 2):
                await call.answer("❌ Ответ должен быть от 0 до 2", show_alert=True)
                return
        else:
            if not (0 <= answer <= 3):
                await call.answer("❌ Ответ должен быть от 0 до 3", show_alert=True)
                return
    except (ValueError, IndexError):
        await call.answer("❌ Ошибка обработки ответа", show_alert=True)
        return
    
    data = await state.get_data()
    question_list = data.get('question_list', [])
    global_n = data.get('global_n')
    
    if not question_list or not global_n:
        await call.answer("❌ Ошибка: данные опроса не найдены", show_alert=True)
        await state.clear()
        return
    
    survey_n = question_list[0]['survey_index']
    
    try:
        await api.add_answer(
            call.from_user.id,
            global_n,
            survey_n,
            question_n,
            str(answer),
            datetime.now().isoformat()
        )
    except Exception as e:
        print(f"Error saving answer: {e}")
        await call.answer("❌ Ошибка сохранения ответа", show_alert=True)
        return
    
    try:
        await call.message.delete()
    except:
        pass

    if question_n >= len(question_list):
        await finish_test(call.message, state)
        return
    
    if question_n < len(question_list):
        comment = get_contextual_comment()
        await call.message.answer(f"✅ {comment}")
    
    question_n += 1
    await state.update_data(question_n=question_n)
    await ask_question(call.message, state)


@router.message(Questions.questions1)
async def handle_gad7_text_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data.get('question_n')
    question_list = data.get('question_list', [])
    global_n = data.get('global_n')
    
    if not question_list or not global_n:
        await message.answer("❌ Ошибка: данные опроса не найдены")
        await state.clear()
        return
    
    survey_n = question_list[0]['survey_index']
    
    if question_n == 11:
        game_name = message.text.strip()
        
        if not game_name or len(game_name) < 2:
            await message.answer("❌ Пожалуйста, введи название игры (минимум 2 символа)")
            return
        
        try:
            await api.add_answer(
                message.from_user.id,
                global_n,
                survey_n,
                question_n,
                game_name,
                datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Error saving answer: {e}")
            await message.answer("❌ Ошибка сохранения ответа")
            return
        
        if question_n >= len(question_list):
            await finish_test(message, state)
            return
        
        question_n += 1
        await state.update_data(question_n=question_n)
        await ask_question(message, state)
        return
    
    try:
        answer_value = int(message.text)
        
        if question_n in [8, 9]:
            if not (0 <= answer_value <= 4):
                await message.answer("❌ Ответ должен быть числом от 0 до 4")
                return
        elif question_n == 10:
            if not (0 <= answer_value <= 2):
                await message.answer("❌ Ответ должен быть числом от 0 до 2")
                return
        else:
            if not (0 <= answer_value <= 3):
                await message.answer("❌ Ответ должен быть числом от 0 до 3")
                return
        
        await api.add_answer(
            message.from_user.id,
            global_n,
            survey_n,
            question_n,
            str(answer_value),
            datetime.now().isoformat()
        )
        
        if question_n >= len(question_list):
            await finish_test(message, state)
            return
        
        question_n += 1
        await state.update_data(question_n=question_n)
        await ask_question(message, state)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введи число. Для вопроса 11 введи название игры текстом.")
        return


@router.callback_query(F.data.startswith("student_answer_"))
async def handle_student_answer(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    parts = call.data.split("_")
    if len(parts) < 4:
        await call.answer("❌ Ошибка формата данных", show_alert=True)
        return
    
    try:
        question_n = int(parts[2])
        answer_value = int(parts[3])
    except (ValueError, IndexError):
        await call.answer("❌ Ошибка обработки ответа", show_alert=True)
        return
    
    answer_map = {
        0: "Нет",
        1: "Скорее нет, чем да",
        2: "Скорее да, чем нет",
        3: "Да"
    }
    answer_text = answer_map.get(answer_value, "Нет")
    
    data = await state.get_data()
    question_list = data.get('question_list', [])
    global_n = data.get('global_n')
    
    if not question_list or not global_n:
        await call.answer("❌ Ошибка: данные опроса не найдены", show_alert=True)
        await state.clear()
        return
    
    survey_n = question_list[0]['survey_index']

    try:
        await api.add_answer(
            call.from_user.id,
            global_n,
            survey_n,
            question_n,
            answer_text,
            datetime.now().isoformat()
        )
    except Exception as e:
        print(f"Error saving answer: {e}")
        await call.answer("❌ Ошибка сохранения ответа", show_alert=True)
        return
    
    try:
        await call.message.delete()
    except:
        pass
    
    if question_n >= len(question_list):
        await finish_test(call.message, state,call.from_user.id)
        return
    
    if question_n < len(question_list):
        comment = get_contextual_comment()
        await call.message.answer(f"✅ {comment}")
    
    question_n += 1
    await state.update_data(question_n=question_n)
    await ask_question(call.message, state)


@router.callback_query(F.data == "progress_info")
async def show_progress_info(call: CallbackQuery):
    await call.answer("Это индикатор прогресса прохождения опроса", show_alert=False)


