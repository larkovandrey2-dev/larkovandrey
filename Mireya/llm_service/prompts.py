import random
from typing import List, Dict

GAD_ANALYSIS_PROMPTS = [
    """Твоя задача — извлечь балл тревожности (0-3) из ответа.
Контекст вопроса: {question}
Ответ пользователя: {answer}

Инструкция:
1. Если пользователь подтверждает наличие симптома ("Да", "Было", "Конечно", "Тяжело", "Напряженно") -> СТАВЬ БАЛЛ 2 или 3 (в зависимости от силы эмоций). НЕ СПРАШИВАЙ ПОДРОБНОСТИ.
2. Если ответ "Иногда", "Редко", "Бывает" -> СТАВЬ БАЛЛ 1.
3. Если отрицание -> СТАВЬ БАЛЛ 0.
4. Если пользователь раздражен ("Я же сказал", "Повторяю") -> СТАВЬ 3.
5. Задавай уточняющий вопрос (верни -1), ТОЛЬКО если ответ вообще не по теме (например, "привет" или "не знаю").

Примеры:
"Очень напряженно" -> 3
"Да, было" -> 2
"Ну так, бывает" -> 1
"Нет" -> 0
Правила:
- Если юзер ответил по сути -> верни 0, 1, 2 или 3.
- Если юзер просит пояснить ("непонятно", "в смысле?") -> верни 'EXPLAIN'.
- Если юзер сливается ("ой все", "забей", "проехали", "скип") -> верни 'SKIP'.
- Иначе -> -1."""
]
CRISIS_VERIFICATION_PROMPT = """
Проанализируй сообщение пользователя на предмет суицидальных намерений или желания нанести себе вред.
Сообщение: "{answer}"

Инструкция:
1. Ответь 'YES', если человек явно говорит о желании умереть, убить себя или нанести вред.
2. Ответь 'YES', если используется суицидальный сленг в серьезном контексте (выпилиться, роскомнадзор).
3. Ответь 'NO', если это просто описание усталости ("я умираю от скуки"), случайные совпадения слов ("выпил воды", "выйти в окно настроек") или шутка.
4. Твой ответ должен содержать ТОЛЬКО одно слово: YES или NO.
"""
SELF_LOVE_PROMPTS = [
    """Оцени ответ (шкала 0-3).
Вопрос: {question}
Ответ: {answer}

- Ответ по сути -> цифра 0-3.
- Не понимает вопрос -> 'EXPLAIN'.
- Не хочет отвечать -> 'SKIP'.
- Иначе -> -1."""
]

GAMING_PROMPTS = {
    9: ["""С кем играет? (0-один, 1-с друзьями).
Если не понимает вопрос -> 'EXPLAIN'.
Если не хочет отвечать -> 'SKIP'.
Иначе цифра 0 или 1.
Вопрос: {question}\nОтвет: {answer}"""],

    10: ["""Платформа? (0-ПК, 1-Консоль, 2-Мобайл).
Если не понимает -> 'EXPLAIN'.
Если отказ -> 'SKIP'.
Иначе цифра 0, 1 или 2.
Вопрос: {question}\nОтвет: {answer}"""],

    11: ["""Название игры?
Если назвал игру -> верни 1.
Если не понимает вопрос -> 'EXPLAIN'.
Если отказ/забей -> 'SKIP'.
Иначе -> -1.
Вопрос: {question}\nОтвет: {answer}"""]
}

STUDENT_SURVEY_PROMPTS = [
    """Оцени ответ (0-3).
Вопрос: {question}
Ответ: {answer}

Логика:
- Есть ответ -> цифра 0-3.
- "Не понимаю", "Чего?" -> 'EXPLAIN'.
- "Забей", "Дальше", "Не знаю" -> 'SKIP'.
- Иначе -> -1."""
]

EXPLAIN_GENERATION_PROMPTS = [
    """Пользователь не понял этот вопрос: "{question}".
Объясни его смысл самыми простыми словами.
ЗАПРЕЩЕНО упоминать баллы, цифры или шкалы. Объясни только суть состояния, о котором идет речь.
Пример: Вместо "Оцените тревогу 0-3" скажи "Речь о том, бывает ли у тебя чувство беспричинного беспокойства".""",

    """Перефразируй вопрос "{question}" максимально доходчиво.
Собеседник запутался. Объясни, что ты имел в виду, не используя сложные термины и цифры. Просто спроси, бывает ли с ним такое."""
]

FOLLOW_UP_GENERATION_PROMPTS = [
    "Пользователь ответил не совсем понятно на вопрос: '{question}'. Придумай мягкий вопрос, чтобы уточнить детали. Не проси цифры.",
    "Твоя цель — понять состояние собеседника. Задай добрый уточняющий вопрос к: '{question}'.",
]

FOLLOW_UP_TEMPLATES = [
    "Можешь рассказать об этом чуть подробнее?",
    "А можешь уточнить, что ты имеешь в виду?",
    "Я немного запутался. Помоги мне понять, как часто это происходит?",
    "А можешь раскрыть эту мысль?",
]

REPHRASE_PROMPTS = [
    """Твоя задача — переписать вопрос для живого диалога в Telegram.
Исходный вопрос: "{question}"

Требования:
1. УДАЛИ любые упоминания шкал, цифр (0, 1, 2, 3) и просьбы оценить баллами.
2. Обращайся на "ты", дружелюбно, но без панибратства.
3. Спрашивай только о самочувствии/состоянии.
4. Вопрос должен требовать текстового ответа, а не цифры.

Пример:
Вход: "Чувствовали ли вы раздражение? (0-нет, 3-сильно)"
Выход: "Слушай, а не замечал за собой в последнее время, что стал чаще раздражаться по пустякам?"
""",

    """Переформулируй этот вопрос, чтобы он звучал мягко и участливо.
Исходный вопрос: "{question}"

ВАЖНО: Исключи из вопроса любые инструкции по баллам (0-3). Не проси оценивать цифрами. Мы хотим, чтобы человек просто рассказал о проблеме словами.
""",

    """Представь, что ты спрашиваешь друга о его делах. Адаптируй этот вопрос:
"{question}"

Убери всю канцелярщину и цифры. Сделай вопрос коротким и человечным. Не упоминай шкалу 0-3."""
]

_used_follow_ups: Dict[str, List[str]] = {}
_max_tracked = 10



def get_explain_prompt(question: str) -> str:
    """Возвращает промпт для объяснения непонятного вопроса."""
    return random.choice(EXPLAIN_GENERATION_PROMPTS).format(question=question)


def get_rephrase_prompt(question: str) -> str:
    template = random.choice(REPHRASE_PROMPTS)
    return template.format(question=question)


def get_analysis_prompt(question: str, answer: str, question_n: int, survey_n: int = 1) -> str:
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