import random
from typing import List, Dict

GAD_ANALYSIS_PROMPTS = [
    """Твоя задача — оценить уровень тревожности по ответу пользователя.
Шкала GAD-7:
0 = Совсем нет, редко, никогда, всё хорошо.
1 = Несколько дней, иногда, бывает, слабо выражено.
2 = Больше половины дней, часто, довольно сильно.
3 = Почти каждый день, постоянно, очень сильно, "Да" (если уверенно).

Вопрос бота: {question}
Ответ пользователя: {answer}

Инструкция:
1. Проанализируй смысл ответа. Слово "Иногда" относи к 1. Простое "Да" относи к 2 или 3 в зависимости от контекста вопроса.
2. Если ответ не содержит явной частоты, оцени эмоциональную окраску (спокойно -> 0, тревожно -> 2-3).
3. Верни ТОЛЬКО цифру (0, 1, 2 или 3).
4. Верни -1 ТОЛЬКО если ответ вообще не имеет смысла или не относится к вопросу (например, набор букв или рассказ про футбол).""",

    """Оцени ответ пользователя по шкале частоты симптомов (0-3).
0: Отсутствие симптома.
1: Редкие проявления (иногда, чуть-чуть).
2: Частые проявления (часто, много).
3: Постоянные/Сильные проявления.

Вопрос: {question}
Ответ: {answer}

Выведи только цифру. Если пользователь просто соглашается ("Да", "Было"), ставь 2. Если отрицает ("Нет"), ставь 0. Если сомневаешься между баллами, выбери тот, который кажется ближе. Верни -1 только при полной бессмыслице."""
]

SELF_LOVE_PROMPTS = [
    """Оцени уровень самопринятия/нарциссизма в ответе.
Шкала:
0 - Самокритика, нелюбовь к себе, неуверенность.
1 - Сомнения, смешанные чувства, "иногда люблю, иногда нет".
2 - Здоровая любовь к себе, принятие, "нормально".
3 - Высокое самомнение, нарциссизм, полная уверенность, "я лучший".

Вопрос: {question}
Ответ: {answer}

Если пользователь пишет "Иногда" или "Бывает" — это скорее 1 (сомнения) или 2 (норма), выбери по контексту негатива/позитива.
Верни ТОЛЬКО цифру. Верни -1, только если ответ нечитаем."""
]

GAMING_PROMPTS = {
    9: [
        """Проанализируй, с кем играет пользователь.
0 = Один, соло, singleplayer.
1 = С друзьями, онлайн, мультиплеер, с кем-то.

Вопрос: {question}
Ответ: {answer}

Верни 0 или 1. Если непонятно - верни 1 (как дефолт для "другое"). Верни -1 только при явном бреде."""
    ],
    10: [
        """Определи игровую платформу.
0 = ПК, компьютер, ноутбук, комп.
1 = Консоль, PlayStation, Xbox, Nintendo, приставка.
2 = Телефон, мобилка, планшет.

Вопрос: {question}
Ответ: {answer}

Верни цифру (0, 1 или 2). Если названо несколько, выбери основное. Если не указано — верни -1."""
    ],
    11: [
        """Извлеки название игры из ответа. Если пользователь назвал игру, верни 1. Если ответ бессмысленный, верни -1.
Вопрос: {question}
Ответ: {answer}"""
    ]
}

STUDENT_SURVEY_PROMPTS = [
    """Оцени ответ студента по шкале согласия/частоты (0-3).
0 = Нет, никогда, не согласен.
1 = Редко, иногда, скорее нет.
2 = Часто, скорее да, бывает.
3 = Да, постоянно, полностью согласен, очень сильно.

Вопрос: {question}
Ответ: {answer}

Интерпретируй "Да" как 2 или 3. "Иногда" как 1.
Верни только наиболее подходящую цифру. Не будь строгим, старайся угадать намерение."""
]

FOLLOW_UP_GENERATION_PROMPTS = [
    "Пользователь ответил не совсем понятно на вопрос: '{question}'. Придумай мягкий, человечный вопрос, чтобы уточнить детали. Не проси цифры. Спроси, что он имел в виду. Максимум 1 предложение.",
    "Твоя цель — понять состояние собеседника. Он ответил уклончиво на: '{question}'. Задай добрый уточняющий вопрос. Избегай канцеляризмов.",
    "На вопрос '{question}' пришел неясный ответ. Спроси по-дружески, чтобы человек раскрыл мысль подробнее. Не дави на него."
]


FOLLOW_UP_TEMPLATES = [
    "Можешь рассказать об этом чуть подробнее? Я не совсем понял.",
    "Интересно. А можешь уточнить, что ты имеешь в виду?",
    "Я немного запутался. Помоги мне понять, как часто это происходит?",
    "А можешь раскрыть эту мысль? Мне важно понять тебя правильно.",
    "Правильно ли я понимаю? Расскажи чуть детальнее, пожалуйста.",
    "Это сложная тема. Можешь пояснить чуть конкретнее?",
]

REPHRASE_PROMPTS = [
    "Переформулируй вопрос, чтобы он звучал как в переписке с другом в Telegram. Сохрани суть, но убери официоз. Не проси оценивать цифрами. Вопрос: {question}",
    "Сделай этот вопрос мягче и человечнее, обращаясь на 'ты'. Избегай фраз типа 'оцени по шкале'. Вопрос: {question}",
    "Представь, что ты заботливый друг. Как бы ты задал этот вопрос? Вопрос: {question}"
]

_used_follow_ups: Dict[str, List[str]] = {}
_max_tracked = 10


def get_rephrase_prompt(question: str) -> str:
    template = random.choice(REPHRASE_PROMPTS)
    return template.format(question=question)


def get_analysis_prompt(question: str, answer: str, question_n: int, survey_n: int = 1) -> str:
    """Выбирает правильный промпт в зависимости от контекста."""

    if survey_n == 1:
        if question_n == 8:
            return SELF_LOVE_PROMPTS[0].format(question=question, answer=answer)
        elif question_n == 9:
            return GAMING_PROMPTS[9][0].format(question=question, answer=answer)
        elif question_n == 10:
            return GAMING_PROMPTS[10][0].format(question=question, answer=answer)
        elif question_n == 11:
            return GAMING_PROMPTS[11][0].format(question=question, answer=answer)
        else:
            template = random.choice(GAD_ANALYSIS_PROMPTS)
            return template.format(question=question, answer=answer)

    elif survey_n == 2:
        template = random.choice(STUDENT_SURVEY_PROMPTS)
        return template.format(question=question, answer=answer)

    return GAD_ANALYSIS_PROMPTS[0].format(question=question, answer=answer)


def get_follow_up_generation_prompt(question: str, attempt: int = 0) -> str:
    template = FOLLOW_UP_GENERATION_PROMPTS[attempt % len(FOLLOW_UP_GENERATION_PROMPTS)]
    return template.format(question=question)


def get_follow_up_template(question: str, question_n: int, attempt: int = 0) -> str:
    question_key = f"q{question_n}"

    if question_key not in _used_follow_ups:
        _used_follow_ups[question_key] = []

    used = _used_follow_ups[question_key]
    available = [t for t in FOLLOW_UP_TEMPLATES if t not in used]

    if not available:
        _used_follow_ups[question_key] = []
        available = FOLLOW_UP_TEMPLATES

    template = random.choice(available)
    _used_follow_ups[question_key].append(template)

    if len(_used_follow_ups[question_key]) > _max_tracked:
        _used_follow_ups[question_key].pop(0)

    return template


def reset_follow_up_tracking(question_n: int):
    question_key = f"q{question_n}"
    if question_key in _used_follow_ups:
        _used_follow_ups[question_key] = []