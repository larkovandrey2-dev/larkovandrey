import random

import aiohttp
import asyncio
import os
import re
from typing import Optional, Dict, List, Union
from dotenv import load_dotenv
import hashlib
from llm_service.prompts import (
    get_analysis_prompt,
    get_follow_up_generation_prompt,
    get_follow_up_template,
    reset_follow_up_tracking,
    get_rephrase_prompt,
    get_explain_prompt,
    CRISIS_VERIFICATION_PROMPT
)

load_dotenv()

YC_API_TOKEN = os.getenv('YC_API_TOKEN')
MODEL_URI = "gpt://b1gcbn4fh3ils5usalqv/yandexgpt-5.1/latest"
HEADERS = {
    "Authorization": f"Bearer {YC_API_TOKEN}",
    "Content-Type": "application/json"
}
HARD_CRISIS_KEYWORDS = [
    "не хочу жить", "жить не хочу", "смысла жить нет", "нет смысла жить",
    "зачем я живу", "лучше бы я умер", "лучше бы я сдох",
    "хочу умереть", "хочу сдохнуть", "мечтаю умереть",
    "ненавижу себя", "я ничтожество", "я обуза", "всем мешаю",
    "без меня будет лучше", "исчезнуть навсегда", "конец всему",
    "суицид", "самоубий",
    "убить себ",
    "покончить с соб",
    "вскрыт", "вскрыл", "вскро",
    "повес", "удав",
    "выпилил", "роскомнадзор", "рипнул"
]

SOFT_CRISIS_KEYWORDS = [
    "окно", "окна", "крыш", "этаж", "высот", "карниз",
    "петля", "веревк", "мыло",
    "таблет", "снотворн", "лекарст",
    "поезд", "электричк", "рельс", "метро",
    "вены", "лезви", "бритв",
    "выпил",
    "смерт", "умир"
]

_prompt_cache: Dict[str, str] = {}
_cache_max_size = 200
_last_follow_ups: Dict[int, List[str]] = {}
_max_tracked_follow_ups = 5


def _get_cache_key(question: str, answer: str) -> str:
    return hashlib.md5(f"{question}:{answer}".encode()).hexdigest()


async def _ask_model_async(prompt: str, temperature: float = 0.0, max_tokens: int = 150, timeout: int = 30) -> Optional[
    Dict]:
    data = {
        "modelUri": MODEL_URI,
        "completionOptions": {"temperature": temperature, "maxTokens": str(max_tokens)},
        "messages": [{"role": "user", "text": prompt}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                    headers=HEADERS, json=data, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"LLM Error: {e}")
        return None


async def explain_question_logic(question: str) -> str:
    prompt = get_explain_prompt(question)
    response = await _ask_model_async(prompt, temperature=0.6, max_tokens=150)
    if response:
        try:
            return response['result']['alternatives'][0]['message']['text'].strip().replace('"', '')
        except:
            pass
    return f"Я имел в виду: {question}. Попробуй ответить своими словами."


async def analyze_question(
        question: str,
        question_n: int,
        answer: str,
        last_json: Optional[Dict[int, int]] = None,
        attempt: int = 0,
        survey_n: int = 1
) -> Union[Dict[int, int], List]:
    if last_json is None:
        last_json = {}
    potential_crisis = False
    answer_lower = answer.lower()
    for word in HARD_CRISIS_KEYWORDS:
        if word in answer_lower:
            return [-999, "CRISIS"]
    potential_crisis = False
    for word in SOFT_CRISIS_KEYWORDS:
        if word in answer_lower:
            potential_crisis = True
            break

    if potential_crisis:
        check_prompt = CRISIS_VERIFICATION_PROMPT.format(answer=answer)

        validation_response = await _ask_model_async(check_prompt, temperature=0.0, max_tokens=10)

        if validation_response:
            try:
                verdict = validation_response['result']['alternatives'][0]['message']['text'].strip().upper()
                if 'YES' in verdict:
                    return [-999, "CRISIS"]
            except:
                pass


    skip_words = ['забей', 'пропусти', 'дальше', 'не хочу', 'ой все', 'хз', 'skip', 'next']
    if any(s in answer.lower() for s in skip_words) and len(answer) < 20:
        last_json[question_n] = 0
        reset_follow_up_tracking(question_n)
        return last_json

    prompt = get_analysis_prompt(question, answer, question_n, survey_n)

    cache_key = _get_cache_key(question, answer)
    if cache_key in _prompt_cache:
        response_text = _prompt_cache[cache_key]
    else:
        api_response = await _ask_model_async(prompt, temperature=0.1,
                                              max_tokens=20)
        if not api_response:
            return last_json
        try:
            response_text = api_response['result']['alternatives'][0]['message']['text'].strip()
        except:
            return last_json

        if len(_prompt_cache) >= _cache_max_size:
            keys_to_remove = list(_prompt_cache.keys())[:_cache_max_size // 2]
            for key in keys_to_remove: _prompt_cache.pop(key, None)
        _prompt_cache[cache_key] = response_text

    response_text = response_text.replace('.', '').replace("'", "").strip()


    if 'SKIP' in response_text:
        last_json[question_n] = 0
        reset_follow_up_tracking(question_n)
        return last_json

    if 'EXPLAIN' in response_text:
        explanation = await explain_question_logic(question)
        return [-1, explanation]

    if response_text.isdigit():
        try:
            score = int(response_text)
            valid = False
            if survey_n == 1:
                if question_n <= 8 and 0 <= score <= 3:
                    valid = True
                elif question_n in [9, 10] and 0 <= score <= 2:
                    valid = True
                elif question_n == 11:
                    valid = True
            else:
                if 0 <= score <= 3: valid = True

            if valid:
                last_json[question_n] = score
                reset_follow_up_tracking(question_n)
                return last_json
        except ValueError:
            pass

    follow_up_question = await _generate_unique_follow_up(question, question_n, attempt)
    return [-1, follow_up_question]


async def _generate_unique_follow_up(original_question: str, question_n: int, attempt: int = 0) -> str:
    if question_n not in _last_follow_ups:
        _last_follow_ups[question_n] = []
    used = _last_follow_ups[question_n]

    generation_prompt = get_follow_up_generation_prompt(original_question, attempt)
    llm_response = await _ask_model_async(generation_prompt, temperature=0.5, max_tokens=100)

    if llm_response:
        try:
            follow_up_text = llm_response['result']['alternatives'][0]['message']['text'].strip()
            follow_up_text = follow_up_text.strip('"\'«»').split('\n')[0].strip()
            if follow_up_text not in used and len(follow_up_text) > 10:
                used.append(follow_up_text)
                if len(used) > _max_tracked_follow_ups: used.pop(0)
                return follow_up_text
        except:
            pass

    for _ in range(10):
        template_text = get_follow_up_template(original_question, question_n, attempt)
        if template_text not in used:
            used.append(template_text)
            if len(used) > _max_tracked_follow_ups: used.pop(0)
            return template_text
        attempt += 1
    return get_follow_up_template(original_question, question_n, attempt)





async def diversify_question(question_text: str) -> str:
    if len(question_text) < 5:
        return question_text
    clean_text = re.sub(r'\(.*?\d.*?\)', '', question_text)
    clean_text = clean_text.replace("от 0 до 3", "").replace("0 - совсем нет", "").replace("3 - очень часто", "")
    clean_text = clean_text.replace("Оцени", "").replace("оцени", "")
    clean_text = " ".join(clean_text.split())
    if len(clean_text) < 5:
        clean_text = question_text

    prompt = get_rephrase_prompt(clean_text)
    api_response = await _ask_model_async(prompt, temperature=0.7, max_tokens=200)

    if not api_response:
        return clean_text

    try:
        new_text = api_response['result']['alternatives'][0]['message']['text'].strip()

        if ":" in new_text[:10]:
            new_text = new_text.split(":", 1)[1].strip()

        new_text = new_text.replace('"', '').replace("«", "").replace("»", "")

        if '0' in new_text and '3' in new_text:
            return clean_text

        if len(new_text) < 5:
            return clean_text

        return new_text

    except (KeyError, IndexError):
        return clean_text


async def get_final_recommendation(score_percent: int) -> str:
    level_desc = "низкий"
    if score_percent > 30: level_desc = "средний"
    if score_percent > 70: level_desc = "высокий"

    focus_areas = [
        "Сделай упор на дыхательные практики и расслабление тела.",
        "Сделай упор на когнитивные техники (работа с мыслями).",
        "Сделай упор на простые бытовые радости и отвлечение.",
        "Сделай упор на физическую активность и сон.",
        "Сделай упор на техники заземления и осознанности."
    ]
    random_focus = random.choice(focus_areas)
    random_salt = random.randint(1, 10000)

    prompt = (
        f"У студента уровень тревожности {score_percent}% ({level_desc}). "
        f"Дай 3 очень кратких, конкретных совета (по 1 предложению). "
        f"{random_focus} "
        "Будь эмпатичным другом. Не советуй идти к врачу. "
        "Советы должны отличаться от стандартных 'просто успокойся'. "
        "ВАЖНО: ИСПОЛЬЗУЙ ТОЛЬКО РУССКИЙ ЯЗЫК. Не используй английские слова или идиомы."
        f"[Random seed: {random_salt}] "
        "Формат:\n1. ...\n2. ...\n3. ..."
    )

    response = await _ask_model_async(prompt, temperature=0.7, max_tokens=200)

    default_text = (
        "1. Попробуй практику глубокого дыхания: вдох на 4 счета, выдох на 6.\n"
        "2. Сделай небольшую паузу и выпей стакан воды.\n"
        "3. Если есть возможность, прогуляйся 10 минут на свежем воздухе."
    )

    if response:
        try:
            text = response['result']['alternatives'][0]['message']['text'].strip()
            return text.replace('"', '')
        except:
            return default_text
    return default_text