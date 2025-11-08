from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton

from bot.states import UserLLM
from bot.services.api import generate_with_ollama
from bot.config import PROMPT

router = Router()

@router.callback_query(F.data.startswith('start_llm_mode'))
async def llm_talk_start(call: types.CallbackQuery,state: FSMContext):
    await call.message.answer("Режим общения активирован. Расскажи о своих проблемах и переживаниях. Можешь писать в свободной форме - я проанализирую твои ответы.")
    await state.set_state(UserLLM.answer)

@router.message(UserLLM.answer)
async def llm_talk_answer(message: types.Message, state: FSMContext):
    user_text = message.text
    prompt = PROMPT + f"Текст для анализа с учетом всех замечаний выше: {user_text}"
    response = await generate_with_ollama(prompt)
    kb = types.ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад 🔙')]],resize_keyboard=True)
    await message.answer(f"Оценка твоего состояния:\n {response}", reply_markup=kb)
    await state.clear()

