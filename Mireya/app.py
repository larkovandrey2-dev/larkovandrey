import asyncio
import json
import logging
import requests
import datetime
import os
import aiohttp
from watchfiles import awatch
import database_scripts
import kbs.inline as inline
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, sticker, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from supabase import create_client, Client
from datetime import date
import scripts

# --- подключение Gemma через Ollama ---
async def generate_with_ollama(prompt: str) -> str:
    url = "http://127.0.0.1:11434/api/generate"
    payload = {"model": "gemma3:1b", "prompt": prompt}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Ollama error {resp.status}: {text}")

            response_text = ""
            async for line in resp.content:
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            response_text += data["response"]
                    except json.JSONDecodeError:
                        continue
            return response_text.strip()

logging.basicConfig(level=logging.INFO)
bot = Bot(token="8466015804:AAEt2BWKawjYRbBxhiinKB3JCZaw0-1NMTU")

dp = Dispatcher()

# --- глобальный словарь режимов пользователей ---
user_modes = {}  # {user_id: "llm" | "survey"}

class UserConfig(StatesGroup):
    age = State()
    sex = State()
    education = State()

class UserChanges(StatesGroup):
    age = State()
    education = State()

class Questions(StatesGroup):
    questions = State()

class Admins(StatesGroup):
    edit_question = State()
    new_question = State()

# --- старт ---
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in await database_scripts.all_users():
        await message.answer('Вы в нашем сервисе впервые. Введите свой возраст')
        await state.set_state(UserConfig.age)
    else:
        async with aiohttp.ClientSession() as session:
            reg_url = f"http://127.0.0.1:8000/api/register_user/{message.from_user.id}"
            await session.get(reg_url)
            user_req = f"http://127.0.0.1:8000/api/get_user/{user_id}"
            resp = await session.get(user_req)
            if resp.status != 200:
                await message.answer("Ошибка при получении данных пользователя.")
                return
            user_data = await resp.json()
            if not user_data:
                await message.answer("Данные пользователя не найдены.")
                return
        keyboard = InlineKeyboardBuilder()
        keyboard.row(types.InlineKeyboardButton(text='Пройти опрос', callback_data='start_test'))
        keyboard.row(types.InlineKeyboardButton(text='Поговорить', callback_data='start_llm'))
        keyboard.row(types.InlineKeyboardButton(text='Личный кабинет', callback_data='personal_lk'))
        username = message.from_user.username
        text = f'''Добро пожаловать, @{username}, я Mireya.
Здесь нет правильных или неправильных ответов - только твои ощущения.
Сейчас мне важно лучше узнать, что ты чувствуешь.
Ты можешь:
Пройти опрос
Поговорить со мной
Открыть личный кабинет'''
        await message.answer(text, reply_markup=keyboard.as_markup())

# --- ввод возраста ---
@dp.message(UserConfig.age)
async def age_setup(message: types.Message, state: FSMContext):
    age = message.text
    if not age.isdigit() or not (12 < int(age) < 100):
        await message.answer('Введите корректный возраст')
    else:
        await state.update_data(age=age)
        kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                 keyboard=[[KeyboardButton(text='Мужской 👨')], [KeyboardButton(text='Женский 👩')]])
        await message.answer('Выберите пол:', reply_markup=kb)
        await state.set_state(UserConfig.sex)

# --- ввод пола ---
@dp.message(UserConfig.sex)
async def sex_setup(message: types.Message, state: FSMContext):
    sex = message.text.split()[0]
    await state.update_data(sex=sex)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await message.answer('Выберите уровень образования: ', reply_markup=kb)
    await state.set_state(UserConfig.education)

# --- ввод образования и завершение настройки ---
@dp.message(UserConfig.education)
async def finish_setup(message: types.Message, state: FSMContext):
    education = message.text
    data = await state.get_data()
    sex = data['sex']
    age = data['age']
    # Register user directly with database_scripts
    await database_scripts.create_user(int(message.from_user.id), 'user', None)
    await asyncio.sleep(1)  # Wait for creation to propagate
    # Verify user exists
    if message.from_user.id in await database_scripts.all_users():
        await database_scripts.change_user_stat(message.from_user.id, 'education', education)
        await database_scripts.change_user_stat(message.from_user.id, 'sex', sex)
        await database_scripts.change_user_stat(message.from_user.id, 'age', int(age))
    else:
        await message.answer("Ошибка при создании пользователя. Попробуйте заново.")
        return
    await state.clear()
    # Send welcome directly to avoid loop
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Пройти опрос', callback_data='start_test'))
    keyboard.row(types.InlineKeyboardButton(text='Поговорить', callback_data='start_llm'))
    keyboard.row(types.InlineKeyboardButton(text='Личный кабинет', callback_data='personal_lk'))
    username = message.from_user.username
    text = f'''Добро пожаловать, @{username}, я Mireya.
Здесь нет правильных или неправильных ответов - только твои ощущения.
Сейчас мне важно лучше узнать, что ты чувствуешь.
Ты можешь:
Пройти опрос
Поговорить со мной
Открыть личный кабинет'''
    await message.answer(text, reply_markup=keyboard.as_markup())
    await bot.send_message(message.chat.id, '.', reply_markup=types.ReplyKeyboardRemove(), disable_notification=True)

# --- личный кабинет ---
@dp.callback_query(F.data.startswith('personal_lk'))
async def personal_lk(call: CallbackQuery, state: FSMContext):
    req = f"http://127.0.0.1:8000/api/get_user/{call.from_user.id}"
    async with aiohttp.ClientSession() as session:
        resp = await session.get(req)
        if resp.status != 200:
            await call.message.answer("Ошибка при получении данных пользователя.")
            return
        data = await resp.json()
        if not data:
            await call.message.answer("Данные пользователя не найдены.")
            return
    text = f'''*Профиль пользователя @{call.from_user.username}*\n
🆔: {call.from_user.id}\n
Пройдено опросов ✔️: {data['surveys_count']}\n
Пол: {'👨' if data['sex'] == 'Мужской' else '👩'}\n
Возраст: {data['age']}\n
Образование 🎓: {data['education']}\n\n'''
    if data['role'] == 'user':
        text += 'Ваша роль: пользователь'
    elif data['role'] == 'admin':
        text += 'Ваша роль: админ (редактор) вопросов'
    elif data['role'] == 'bot_admin':
        text += 'Ваша роль: админ бота'
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Изменить возраст",callback_data="lk_change_age"))
    builder.row(InlineKeyboardButton(text="Изменить пол",callback_data="lk_change_sex"))
    builder.row(InlineKeyboardButton(text="Изменить образование",callback_data="lk_change_education"))
    await call.message.answer(text,parse_mode=ParseMode.MARKDOWN,reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith('lk_change_sex'))
async def lk_change_sex(call: CallbackQuery):
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    sex = user_data['sex']
    if sex == 'Мужской':
        await database_scripts.change_user_stat(int(call.from_user.id), 'sex','Женский')
    else:
        await database_scripts.change_user_stat(int(call.from_user.id), 'sex', 'Мужской')
    await call.message.delete()
    await personal_lk(call)

@dp.callback_query(F.data.startswith('lk_change_age'))
async def lk_change_age(call: CallbackQuery,state: FSMContext):
    await call.message.delete()
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    await call.message.answer("Введите свой возраст: ")
    await state.set_state(UserChanges.age)
    await state.update_data(callback=call)

@dp.message(UserChanges.age)
async def lk_change_age_commit(message: types.Message,state: FSMContext):
    age = message.text
    data = await state.get_data()
    if not age.isdecimal() or not(12 < int(age) < 100):
        await message.answer('Введите корректный возраст: ')
    else:
        await database_scripts.change_user_stat(message.from_user.id, 'age', int(age))
        await personal_lk(data['callback'])
        await state.clear()

@dp.callback_query(F.data.startswith('lk_change_education'))
async def lk_change_education(call: CallbackQuery,state: FSMContext):
    user_data = await database_scripts.get_user_stats(call.from_user.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Высшее образование')],
                                                             [KeyboardButton(text='Основное общее образование')],
                                                             [KeyboardButton(text='Среднее общее')]])
    await call.message.delete()
    await call.message.answer('Выберите уровень образования: ',reply_markup=kb)
    await state.set_state(UserChanges.education)
    await state.update_data(callback=call)

@dp.message(UserChanges.education)
async def lk_change_education_commit(message: types.Message,state: FSMContext):
    education = message.text
    data = await state.get_data()
    if education not in ['Высшее образование','Основное общее образование','Среднее общее']:
        await message.answer('Выберите корректный уровень образования: ')
    else:
        await database_scripts.change_user_stat(message.from_user.id, 'education', education)
        await message.answer('Изменение успешно!',reply_markup=types.ReplyKeyboardRemove())
        await personal_lk(data['callback'])
        await state.clear()

# --- админка ---
@dp.message(Command('admin'))
async def admin_command(message: types.Message):
    user_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        user_req = f"http://127.0.0.1:8000/api/get_user/{user_id}"
        resp = await session.get(user_req)
        if resp.status != 200:
            await message.answer("Ошибка при получении данных пользователя.")
            return
        user_data = await resp.json()
        if not user_data:
            await message.answer("Данные пользователя не найдены.")
            return
    if user_data['role'] in ['admin', 'bot_admin']:
        builder = await inline.create_admin_commands()
        await message.answer('Доступ разрешен. Выберите действие: ', reply_markup=builder.as_markup())
    else:
        await message.answer('Доступ запрещен.')

@dp.callback_query(F.data.startswith('admin_delete_questions'))
async def admin_delete_questions_list(call: CallbackQuery):
    questions = await database_scripts.all_questions()
    kb = await inline.create_deletion_question_list(questions)
    await call.message.answer('Выберите из списка вопрос, который хотите удалить:', reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith('delete_question'))
async def delete_question(call: CallbackQuery):
    await call.message.delete()
    data = call.data.split('_')
    survey_index = int(data[2])
    question_index = int(data[3])
    await database_scripts.delete_question(question_index, survey_index)
    async with aiohttp.ClientSession() as session:
        response = (await (await session.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}")).json())['data']
    if response:
        first_question_index = int(response[0]['question_index'])
        for i in range(1, len(response)):
            await database_scripts.change_question_index(int(response[i]['question_index']), int(response[i]['survey_index']),
                                                   first_question_index + i + 1)
    await call.message.answer('Удаление успешно')
    await admin_delete_questions_list(call)

@dp.callback_query(F.data.startswith('admin_show_questions'))
async def admin_show_questions_actions(call: CallbackQuery):
    user_id = call.from_user.id
    async with aiohttp.ClientSession() as session:
        user_req = f"http://127.0.0.1:8000/api/get_user/{user_id}"
        resp = await session.get(user_req)
        if resp.status != 200:
            await call.message.answer("Ошибка при получении данных пользователя.")
            return
        user_data = await resp.json()
        if not user_data:
            await call.message.answer("Данные пользователя не найдены.")
            return
    if user_data['role'] in ['admin', 'bot_admin']:
        questions = await database_scripts.all_questions()
        kb = await inline.create_edit_questions_kb(questions)
        await call.message.answer(
            'Ниже представлена информация в виде: номер опроса || текст вопроса. Можете менять вопросы и создавать новые',
            reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith('new_question'))
async def new_question_start(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Введите новый текст для вопроса в формате: номер опроса | текст вопроса')
    await state.set_state(Admins.new_question)

@dp.callback_query(F.data.startswith('change_question'))
async def edit_question(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    survey_index = data[2]
    question_index = data[3]
    await call.message.answer(f'Введите новый текст для вопроса {question_index} из опроса {survey_index}')
    await state.update_data(question_index=question_index)
    await state.update_data(survey_index=survey_index)
    await state.set_state(Admins.edit_question)

@dp.message(Admins.new_question)
async def new_question(message: types.Message, state: FSMContext):
    msg = message.text.split('|')
    survey_index = int(msg[0])
    quest_text = msg[1]
    quest_index = 1
    try:
        async with aiohttp.ClientSession() as session:
            response = (await (await session.get(f"http://127.0.0.1:8000/api/get_questions/{survey_index}")).json())
        if response['data']:
            quest_index = response['data'][-1]['question_index'] + 1
    except Exception as e:
        print(e)
    await database_scripts.add_question(quest_index, survey_index, quest_text)
    await state.clear()
    await admin_command(message)

@dp.message(Admins.edit_question)
async def commit_question(message: types.Message, state: FSMContext):
    edited_question = message.text
    data = await state.get_data()
    await database_scripts.change_question(int(data['question_index']), int(data['survey_index']), edited_question)
    await message.answer('Успешно изменен вопрос')
    await admin_command(message)
    await state.clear()

# --- запуск режима LLM ---
@dp.callback_query(F.data == "start_llm")
async def start_llm_mode(callback: types.CallbackQuery):
    user_modes[callback.from_user.id] = "llm"
    await callback.message.answer("Режим общения активирован. Можешь писать в свободной форме - я проанализирую твои ответы.")
    await callback.answer()

# --- запуск опроса ---
@dp.callback_query(F.data.startswith("start_test"))
async def start_test(call: CallbackQuery, state: FSMContext):
    user_modes[call.from_user.id] = "survey"
    await state.clear()
    url = f"http://127.0.0.1:8000/api/{call.from_user.id}/get_question_list"
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url)
        if resp.status != 200:
            await call.message.answer("Ошибка загрузки вопросов.")
            return
        data = await resp.json()
        if data is None:
            await call.message.answer("Данные вопросов не получены.")
            return
        questions = data if isinstance(data, list) else data.get('data', [])
        if not questions:
            await call.message.answer("Не удалось загрузить вопросы или нет вопросов.")
            return
    global_surveys_n = list(set(await database_scripts.all_global_attempts()))
    global_surveys_n.sort()
    if not global_surveys_n:
        global_surveys_n = [0]
    await state.update_data(question_list=questions)
    await state.update_data(question_n=1)
    await state.update_data(global_n=global_surveys_n[-1] + 1)
    await state.set_state(Questions.questions)
    await ask_question(call.message, state)
    await call.answer()

# --- функция для вопроса ---
async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_n = data['question_n']
    question_list = data['question_list']
    current_question = [i['question_text'] for i in question_list if i['question_index'] == question_n][0]
    await message.answer(current_question)

# --- обработка сообщений (объединено с finish_test и message_test) ---
@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "survey")
    current_state = await state.get_state()

    # --- Режим LLM ---
    if mode == "llm":
        user_text = message.text
        prompt = f"""
Дан текст: "{user_text}". Исходя из этого текста ответь на следующий вопрос:
1. На сколько часто нервничал, тревожився или испытывал сильный стресс автор этого текста в течение последних 2 недель?
2. На сколько часто был неспособен успокоиться или контролировать свое волнение автор этого текста в течение последних 2 недель?
3. На сколько часто слишком сильно волновался по различным поводам автор этого текста в течение последних 2 недель?
4. На сколько часто автору данного текста было трудно расслабится в течение последних 2 недель?
5. На сколько часто автор данного тескта был настолько суетлив, что ему было тяжело усидеть на месте в течение последних 2 недель?
6. На сколько часто легко злился или раздражался автор текста в течение последних 2 недель?
7. На сколько часто автор этого текста испытывал страх, словно должно произойти нечто ужасное в течение последних 2 недель?
Можно делать предположения. Ответ должен быть числом от 0 до 3 в зависимости от частоты. В ответе должны содержаться только цифры. В случае недостатка данных выведи -1.
        """
        await message.answer("Анализирую твое сообщение...")
        response = await generate_with_ollama(prompt)
        await message.answer(f"Оценка твоего состояния:\n{response}\nНажми /start чтобы вернуться в меню.")
        return

    # --- Режим опроса ---
    elif mode == "survey" and current_state == "Questions:questions":
        data = await state.get_data()
        question_list = data.get("question_list", [])
        question_n = data.get("question_n", 1)
        text = message.text
        global_n = data['global_n']
        survey_n = question_list[0]['survey_index']

        # Проверка для последнего вопроса (про игру)
        if question_n == len(question_list):
            valid_games = ["League of Legends", "Other", "Starcraft 2", "Counter Strike", "World of Warcraft", "Hearthstone", "Diablo 3", "Heroes of the Storm", "Guild Wars 2", "Skyrim", "Destiny"]
            if text not in valid_games:
                await message.answer("Пожалуйста, введите название игры или 'Other'.")
                return

        async with aiohttp.ClientSession() as session:
            await session.get(
                f"http://127.0.0.1:8000/api/add_question/{message.from_user.id}&{survey_n}&{question_n}&{text}&{global_n}&{datetime.datetime.now()}")

        # Проверяем, первые ли это 7 вопросов GAD7
        is_gad_question = question_n <= 7
        if is_gad_question:
            try:
                answer_value = int(text)
            except ValueError:
                await message.answer("Пожалуйста, введи число от 0 до 3.")
                return
            if answer_value < 0 or answer_value > 3:
                await message.answer("Ответ должен быть числом от 0 до 3.")
                return

        if question_n == len(question_list):
            # --- Завершение опроса (finish_test) ---
            user_data = await database_scripts.get_user_stats(message.from_user.id)
            surveys_user_c = user_data['surveys_count']
            results_list = user_data['all_user_global_attempts']
            if results_list is None:
                results_list = []
            results_list.append(global_n)
            if surveys_user_c is None:
                surveys_user_c = 0
            await database_scripts.change_user_stat(message.from_user.id, 'last_survey_index', survey_n)
            await database_scripts.change_user_stat(message.from_user.id, 'surveys_count', surveys_user_c + 1)
            await database_scripts.change_user_stat(message.from_user.id, 'all_user_global_attempts', results_list)
            await state.clear()
            user_answers = [i['response_text'] for i in await database_scripts.get_answers_by_global_attempt(int(global_n))]
            ans_form = await scripts.form_gad7_survey_1(user_answers, user_data['sex'], user_data['age'], user_data['education'])
            predicted_level = await scripts.predict_stress_level(ans_form)
            await message.answer(f'Опрос заверешен. Твои ответы получены. Предполагаемый уровень стресса/тревожности: {predicted_level}%\nНажми /start чтобы вернуться в меню.')
            await database_scripts.add_survey_result(message.from_user.id, global_n, survey_n, str(datetime.datetime.now().strftime('%Y-%M-%D %H:%M:%S')), predicted_level)
            return

        question_n += 1
        await state.update_data(question_n=question_n)
        await ask_question(message, state)

    # Сообщения вне опроса
    elif mode == "survey" and (current_state is None):
        await message.answer("Сейчас активен режим опроса. Для начала нажми кнопку «Пройти опрос» или /start.")

# --- запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())