import random
from typing import List


PROCESSING_MESSAGES = [
    "💭 Анализирую твой ответ...",
    "🤔 Обрабатываю информацию...",
    "✨ Размышляю над ответом...",
    "🔍 Изучаю детали...",
    "📝 Записываю ответ...",
    "💡 Обрабатываю данные...",
    "🎯 Анализирую...",
    "📊 Оцениваю ответ...",
    "💫 Обрабатываю...",
    "🌟 Разбираюсь в деталях...",
]

_last_processing_message: str = ""


def get_processing_message() -> str:
    global _last_processing_message
    
    available = [msg for msg in PROCESSING_MESSAGES if msg != _last_processing_message]
    if not available:
        available = PROCESSING_MESSAGES
    
    message = random.choice(available)
    _last_processing_message = message
    return message


CONTEXTUAL_COMMENTS = [
    "Продолжаем...",
    "Следующий вопрос...",
    "Ещё немного...",
    "Почти готово...",
    "Отлично, продолжаем...",
]


def get_contextual_comment() -> str:
    return random.choice(CONTEXTUAL_COMMENTS)


EMOJI_PROGRESS = ["⚪", "🟡", "🟠", "🟢", "🔵", "🟣", "🟤", "⚫"]


def get_progress_emoji(current: int, total: int) -> str:
    if total == 0:
        return "⚪"
    
    percentage = (current / total) * 100
    if percentage < 20:
        return "⚪"
    elif percentage < 40:
        return "🟡"
    elif percentage < 60:
        return "🟠"
    elif percentage < 80:
        return "🟢"
    elif percentage < 100:
        return "🔵"
    else:
        return "🟣"


