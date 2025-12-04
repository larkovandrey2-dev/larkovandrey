import html
import os
import re

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import UserChanges
from helpers.database import DatabaseService
import helpers.api as api
from bot.utils.keyboards import build_profile_menu, build_chart_selector, build_back_button

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)
router = Router()


@router.callback_query(F.data == "personal_lk")
@router.callback_query(F.data.startswith('personal_lk'))
async def personal_lk(call: CallbackQuery):
    await call.answer()
    await db.create_client()
    
    user_data = await api.get_user(call.from_user.id)
    if not user_data:
        await call.message.answer("❌ Ошибка загрузки данных. Попробуй позже.")
        return

    username = html.escape(call.from_user.username or call.from_user.first_name)
    role_emoji = "🛡️" if user_data.get('role') == 'admin' else "👤"
    role_name = "Администратор" if user_data.get('role') == 'admin' else "Пользователь"
    trusted_phone = user_data.get('trusted_phone')
    if trusted_phone:
        sos_status = f"✅ <code>{trusted_phone}</code>"
    else:
        sos_status = "⚠️ <b>Не установлен</b>"

    text = (
        f"{role_emoji} <b>{username}</b>\n"
        f"└ ID: <code>{call.from_user.id}</code>\n\n"

        f"📊 <b>Твоя активность</b>\n"
        f"└ Пройдено опросов: <b>{user_data.get('surveys_count', 0)}</b>\n\n"

        f"🪪 <b>Личные данные</b>\n"
        f"▫️ {user_data.get('age', '--')} лет, {user_data.get('sex', 'пол не указан')}\n"
        f"▫️ {user_data.get('education', 'Образование не указано')}\n\n"

        f"🚨 <b>SOS-контакт</b>\n"
        f"└ {sos_status}"
    )
    
    await call.message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_profile_menu()
    )


@router.callback_query(F.data.startswith('sos_info'))
async def sos_button_handler(call: CallbackQuery):
    user_data = await api.get_user(call.from_user.id)
    trusted_phone = user_data.get('trusted_phone')
    text = (
        "<b>🔴 SOS • МНЕ НУЖНА ПОМОЩЬ</b>\n"
        "<i>Мошенники • Угрозы • Кризис</i>\n"
        "──────────────\n\n"
    )
    if trusted_phone:
        text += (
            "🫂 <b>ТВОЙ БЛИЗКИЙ ЧЕЛОВЕК</b>\n"
            f"└ 📞 <code>{trusted_phone}</code>\n\n"
        )
    else:
        text += (
            "⚪️ <i>Доверенный контакт не указан</i>\n"
            "└ <i>(Можно добавить в Личном кабинете)</i>\n\n"
        )

    text += (
        "<b>🎓 УНИВЕРСИТЕТ (МАИ)</b>\n"
        "<i>Зам. по воспитательной работе</i>\n"
        "└ 📞 <code>+7 499 158-09-06</code>\n\n"

        "<b>👮‍♂️ ПОЛИЦИЯ / МВД</b>\n"
        "<i>Если угрожают мошенники или есть опасность</i>\n"
        "└ 📞 <code>102</code> или <code>112</code>\n\n"

        "<b>💜 ПСИХОЛОГИЧЕСКАЯ ПОМОЩЬ</b>\n"
        "<i>Анонимно, бесплатно, круглосуточно</i>\n"
        "└ 📞 <code>8 800 200-01-22</code>"
    )

    await call.message.answer(text, parse_mode="HTML",reply_markup=build_back_button())


def is_valid_phone(text: str) -> bool:
    clean_phone = re.sub(r'[\s\-\(\)]', '', text)
    return bool(re.match(r'^\+?\d{10,15}$', clean_phone))

@router.callback_query(F.data == "lk_set_sos")
async def start_set_phone(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите номер телефона близкого человека для кнопки SOS (начинайте с +7 или 8):")
    await state.set_state(UserChanges.sos_contact)

@router.message(UserChanges.sos_contact)
async def process_phone_input(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    if not is_valid_phone(user_input):
        await message.answer(
            "❌ <b>Это не похоже на номер телефона.</b>\n\n"
            "Пожалуйста, введи только цифры. Можно использовать +, скобки и пробелы.\n"
            "Попробуй ещё раз:",
            parse_mode="HTML"
        )
        return
    clean_phone = re.sub(r'[\s\-\(\)]', '', user_input)
    try:
        await db.change_user_stat(message.from_user.id, "trusted_phone", clean_phone)
        await message.answer(
            f"✅ <b>Контакт сохранен!</b>\n"
            f"Номер: <code>{clean_phone}</code>\n\n"
            f"Теперь он появится, если ты нажмешь кнопку SOS.",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        print(f"Error saving phone: {e}")
        await message.answer("❌ Ошибка при сохранении. Попробуй позже.")
        await state.clear()
@router.callback_query(F.data == "lk_chart_chose")
@router.callback_query(F.data.startswith('lk_chart_chose'))
async def choose_lk_chart(call: CallbackQuery):
    await call.answer()
    await db.create_client()

    data = await db.get_surveys_results(call.from_user.id)

    print(f"Все результаты для пользователя {call.from_user.id}: {data}")

    if not data:
        await call.message.answer(
            "📊 У тебя пока нет данных для графика.\n\n"
            "Пройди опрос, чтобы увидеть динамику.",
            reply_markup=build_back_button("personal_lk")
        )
        return

    surveys_n = sorted(set([item["survey_index"] for item in data]))
    print(f"Найденные survey_index: {surveys_n}")

    if not surveys_n:
        await call.message.answer(
            "📊 Данные для графика отсутствуют. Проверь, что результаты опросов записаны.",
            reply_markup=build_back_button("personal_lk")
        )
        return

    await call.message.answer(
        "📈 <b>Выбери опрос для просмотра графика:</b>",
        parse_mode="HTML",
        reply_markup=build_chart_selector(surveys_n)
    )

@router.callback_query(F.data.startswith('lk_anxiety_chart_'))
async def lk_anxiety_chart(call: CallbackQuery):
    await call.answer("Генерирую график...")
    survey_n = int(call.data.split('_')[3])
    
    processing_msg = await call.message.answer("📊 Генерирую график...")
    
    img_buffer = await db.create_results_chart(call.from_user.id, survey_n)
    
    try:
        await processing_msg.delete()
    except:
        pass
    
    if img_buffer:
        input_file = BufferedInputFile(
            file=img_buffer.getvalue(),
            filename=f"anxiety_chart_{survey_n}.png"
        )
        await call.message.answer_photo(
            photo=input_file,
            caption=f"📈 <b>Динамика уровня тревожности</b>\n\nОпрос {survey_n}",
            parse_mode="HTML"
        )
        img_buffer.close()
    else:
        await call.message.answer(
            "❌ Не удалось создать график.\n\n"
            "Убедись, что есть данные для отображения.",
            reply_markup=build_back_button("lk_chart_chose")
        )


@router.callback_query(F.data.startswith('lk_change_sex'))
async def lk_change_sex(call: CallbackQuery):
    await call.answer()
    await db.create_client()
    user_data = await db.get_user_stats(call.from_user.id)
    current_sex = user_data.get('sex', 'Мужской')
    new_sex = 'Женский' if current_sex == 'Мужской' else 'Мужской'
    
    await db.change_user_stat(call.from_user.id, 'sex', new_sex)
    await call.message.answer(f"✅ Пол изменён на: <b>{new_sex}</b>", parse_mode="HTML")
    
    # Show updated profile button
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Обновить профиль", callback_data="personal_lk"))
    await call.message.answer("Нажми, чтобы обновить профиль:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('lk_change_age'))
async def lk_change_age(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(
        "🎂 <b>Введи свой возраст:</b>\n\n"
        "От 15 до 99 лет",
        parse_mode="HTML"
    )
    await state.set_state(UserChanges.age)
    await state.update_data(callback=call)


@router.message(UserChanges.age)
async def lk_change_age_commit(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if not (15 <= age <= 99):
            await message.answer('❌ Пожалуйста, введи корректный возраст (от 15 до 99 лет)')
            return
    except ValueError:
        await message.answer('❌ Пожалуйста, введи число')
        return
    
    await db.change_user_stat(message.from_user.id, 'age', age)
    await state.clear()
    
    await message.answer('✅ Возраст успешно изменён!', reply_markup=types.ReplyKeyboardRemove())
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Посмотреть профиль", callback_data="personal_lk"))
    await message.answer("Нажми, чтобы посмотреть обновлённый профиль:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('lk_change_education'))
async def lk_change_education(call: CallbackQuery, state: FSMContext):
    await call.answer()
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='🎓 Высшее образование')],
            [KeyboardButton(text='📚 Основное общее образование')],
            [KeyboardButton(text='📖 Среднее общее')]
        ]
    )
    await call.message.answer(
        '🎓 <b>Выбери уровень образования:</b>',
        parse_mode="HTML",
        reply_markup=kb
    )
    await state.set_state(UserChanges.education)
    await state.update_data(callback=call)


@router.message(UserChanges.education)
async def lk_change_education_commit(message: types.Message, state: FSMContext):
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
    
    await db.change_user_stat(message.from_user.id, 'education', matched_education)
    await state.clear()
    
    await message.answer('✅ Образование успешно изменено!', reply_markup=types.ReplyKeyboardRemove())
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Посмотреть профиль", callback_data="personal_lk"))
    await message.answer("Нажми, чтобы посмотреть обновлённый профиль:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith('psycho_info'))
async def psycho_info(call: CallbackQuery, state: FSMContext):
    info_text = """🧠 Психологическая помощь МАИ
Бесплатная и конфиденциальная поддержка студентам при стрессе, тревоге, трудностях в учёбе и общении.
Контакты:
Грищук Е.А.
📞 <code>+7 977 166-84-00</code>
Лысакова А.Н.
📞 <code>+7 903 184-05-00</code>
Пчельникова О.Г.
📞 <code>+7 915 214-27-37</code>
Курочка З.Р.
📞 <code>+7 985 536-80-80</code>
"""
    await call.message.answer_photo(caption=info_text, parse_mode="HTML", reply_markup=build_back_button(),photo="https://mai.ru/upload/iblock/2fe/a9vdhnk3q8tvr7xbvi81klgbo2fw6cs2/Psikhologicheskaya-pomoshch.png")

