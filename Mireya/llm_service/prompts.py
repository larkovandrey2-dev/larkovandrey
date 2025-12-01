"""LLM prompt templates with variations."""
import random
from typing import List, Dict


# Main analysis prompt variations
ANALYSIS_PROMPTS = {2:[
    "Прочитай ответ пользователя и оцени его по шкале: 'да' - 3, 'скорее да' - 2, 'скорее нет' - 1, 'нет' - 0. Если ответ неоднозначен, оцени по контексту. Если данных недостаточно, верни -1. Ответ только числом.\nВопрос: {question}\nОтвет: {answer}",
    "Оцени ответ пользователя числом от 0 до 3: 'да'=3, 'скорее да'=2, 'скорее нет'=1, 'нет'=0. При неоднозначности используй контекст. Если данных мало, верни -1. Только число.\nВопрос: {question}\nОтвет: {answer}",
    "Преобразуй ответ в число: да=3, скорее да=2, скорее нет=1, нет=0. Если неясно, используй контекст. При недостатке данных верни -1. Ответ - только число.\nВопрос: {question}\nОтвет: {answer}",
    "Проанализируй ответ и поставь оценку: да=3, скорее да=2, скорее нет=1, нет=0. Если информации недостаточно для оценки, верни -1. Только число.\nВопрос: {question}\nОтвет: {answer}",
    "Оцени по шкале 0-3: да=3, скорее да=2, скорее нет=1, нет=0. Если ответ неоднозначен, используй контекст. При недостатке данных верни -1.\nВопрос: {question}\nОтвет: {answer}"],
    1: [   "Проанализируй ответ на вопрос о тревожности. Оцени частоту симптомов: 'совсем нет/редко' = 0, 'несколько дней' = 1, 'больше половины дней/часто' = 2, 'почти каждый день/постоянно' = 3. Если ответ размытый, используй контекст. Если данных нет, верни -1. Только число.\nВопрос: {question}\nОтвет: {answer}",
    "Оцени степень выраженности симптома (0-3): 0=нет, 1=иногда, 2=часто, 3=постоянно. Основывайся на ответе пользователя. Если непонятно — верни -1.\nВопрос: {question}\nОтвет: {answer}",
    "Преобразуй ответ в балл GAD-7: 0 (не беспокоит), 1 (иногда), 2 (часто), 3 (очень часто). Верни только цифру. Если нужно уточнение, верни -1.\nВопрос: {question}\nОтвет: {answer}"]
}

SELF_LOVE_PROMPTS = [
    "Оцени уровень любви к себе и самопринятия в ответе пользователя по шкале 0-3. 0 - полная нелюбовь/самокритика, 1 - скорее низкая, 2 - нормальная/здоровая, 3 - высокая/нарциссизм или полная уверенность. Верни -1, если ответ не по теме.\nВопрос: {question}\nОтвет: {answer}",
    "Проанализируй отношение пользователя к себе. Поставь балл: 0 (не любит себя), 1 (сомневается), 2 (принимает себя), 3 (любит/высоко ценит). Только число.\nВопрос: {question}\nОтвет: {answer}"
]
GAMING_PROMPTS = [
    "Проанализируй ответ про компьютерные игры. Определи степень увлеченности (вовлеченности) числом: 0 - не играет/не интересно, 1 - играет редко/мобилки/таймкиллеры, 2 - играет регулярно/любитель, 3 - заядлый геймер/киберспорт/играет постоянно. Если непонятно, верни -1.\nВопрос: {question}\nОтвет: {answer}",
    "Классифицируй гейминг пользователя: 0=не играет, 1=казуальный игрок, 2=активный игрок, 3=хардкорный игрок. Верни только цифру соответствия.\nВопрос: {question}\nОтвет: {answer}"
]

# Follow-up question generation prompts (varied)
FOLLOW_UP_GENERATION_PROMPTS = [
    "Составь короткий уточняющий вопрос (до 150 символов) к следующему вопросу. Начни с 'Уточни, пожалуйста' или 'Расскажи, пожалуйста'. Вопрос должен быть уважительным и спокойным. Исходный вопрос: {question}",
    "Создай короткий уточняющий вопрос (до 150 символов) на основе: {question}. Начни с 'Помоги понять' или 'Расскажи подробнее'. Будь дружелюбным и тёплым.",
    "Придумай короткий уточняющий вопрос (до 150 символов) к: {question}. Начни с 'Можешь уточнить' или 'Расскажи больше'. Сохраняй спокойный и поддерживающий тон.",
    "Составь короткий уточняющий вопрос (до 150 символов) для: {question}. Используй фразы типа 'Помоги разобраться' или 'Расскажи детальнее'. Будь понимающим и мягким.",
    "Создай короткий уточняющий вопрос (до 150 символов) к: {question}. Начни с 'Уточни, если не сложно' или 'Расскажи подробнее, пожалуйста'. Сохраняй дружелюбный тон.",
]

# Fallback follow-up templates (many variations to avoid repetition)
FOLLOW_UP_TEMPLATES = [
    "Уточни, пожалуйста: {question}. Ответь коротко и конкретно.",
    "Чтобы лучше понять, расскажи подробнее: {question}",
    "Мне нужно больше деталей. Можешь уточнить: {question}?",
    "Помоги мне понять лучше. Расскажи: {question}",
    "Нужно немного больше информации. Уточни, пожалуйста: {question}",
    "Чтобы продолжить, мне нужно больше деталей. Расскажи: {question}",
    "Помоги разобраться. Можешь уточнить: {question}?",
    "Чтобы лучше понять твою ситуацию, расскажи подробнее: {question}",
    "Мне нужно больше контекста. Уточни, пожалуйста: {question}",
    "Помоги мне понять. Расскажи детальнее: {question}",
    "Чтобы продолжить анализ, мне нужны дополнительные детали. Уточни: {question}",
    "Помоги разобраться в ситуации. Расскажи подробнее: {question}",
    "Мне нужно больше информации для понимания. Уточни, пожалуйста: {question}",
    "Чтобы лучше понять твоё состояние, расскажи: {question}",
    "Помоги мне понять контекст. Можешь уточнить: {question}?",
]
REPHRASE_PROMPTS = [
    "Переформулируй следующий вопрос, сохранив его точный смысл. Сделай его немного более живым и разговорным и обращайся на ты, как с другом. Не используй сложные обороты. Вопрос: {question}",
    "Измени формулировку этого вопроса, чтобы он звучал мягче и участливее, но смысл остался тем же и обращайся на ты, как с другом. Вопрос: {question}",
    "Задай этот же вопрос другими словами. Используй дружелюбный тон и обращайся на ты, как с другом. Вопрос: {question}",
    "Представь этот вопрос немного иначе, чтобы разнообразить диалог. Сохрани суть и обращайся на ты, как с другом. Вопрос: {question}"
]


# Track used follow-up questions to avoid repetition
_used_follow_ups: Dict[str, List[str]] = {}
_max_tracked = 10

def get_rephrase_prompt(question: str) -> str:
    """Selects a random prompt to rephrase the question."""
    template = random.choice(REPHRASE_PROMPTS)
    return template.format(question=question)
def get_analysis_prompt(question: str, answer: str, question_n: int, survey_n: int = 1) -> str:
    """Get a varied analysis prompt."""
    if survey_n == 1:
        if question_n <= 7:
            template = ANALYSIS_PROMPTS[1][question_n % len(ANALYSIS_PROMPTS[1])]
        elif question_n == 8:
            template = SELF_LOVE_PROMPTS[question_n % len(SELF_LOVE_PROMPTS)]
        else:
            template = GAMING_PROMPTS[question_n % len(GAMING_PROMPTS)]

    elif survey_n == 2:
        template = ANALYSIS_PROMPTS[2][question_n % len(ANALYSIS_PROMPTS[2])]
    return template.format(question=question, answer=answer)


def get_follow_up_generation_prompt(question: str, attempt: int = 0) -> str:
    """Get a varied follow-up generation prompt."""
    template = FOLLOW_UP_GENERATION_PROMPTS[attempt % len(FOLLOW_UP_GENERATION_PROMPTS)]
    return template.format(question=question)


def get_follow_up_template(question: str, question_n: int, attempt: int = 0) -> str:
    """Get a follow-up template that hasn't been used recently for this question."""
    # Track used templates per question
    question_key = f"q{question_n}"
    
    if question_key not in _used_follow_ups:
        _used_follow_ups[question_key] = []
    
    used = _used_follow_ups[question_key]
    
    # Get available templates
    available = [t for t in FOLLOW_UP_TEMPLATES if t not in used]
    
    # If all used, reset for this question
    if not available:
        _used_follow_ups[question_key] = []
        available = FOLLOW_UP_TEMPLATES
    
    # Select template
    template = random.choice(available)
    
    # Track it
    _used_follow_ups[question_key].append(template)
    
    # Limit tracking size
    if len(_used_follow_ups[question_key]) > _max_tracked:
        _used_follow_ups[question_key].pop(0)
    
    return template.format(question=question)


def reset_follow_up_tracking(question_n: int):
    """Reset tracking for a specific question."""
    question_key = f"q{question_n}"
    if question_key in _used_follow_ups:
        _used_follow_ups[question_key] = []


