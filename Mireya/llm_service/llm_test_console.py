import requests
import re
import asyncio
from statistics import mean

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b-instruct-q4_k_m"

QUESTIONS = [
     "Не могли ли вы заснуть или спали плохо?",
     "Было ли такое, что вы не хотели есть или ели слишком много?",
     "Были ли резкие перепады настроения без причины?",
     "Не могли ли вы сдержать своё волнение?",
     "Было ли трудно усидеть на месте из-за нехватки времени?",
     "Есть ли среди ваших заданий особенно сложные или непонятные?",
     "Кажется ли вам, что вокруг вас одни гении?",
     "Есть ли у вас другие проблемы, о которых хотите рассказать?"
]

NUM_QUESTIONS = len(QUESTIONS)
MAX_PER_QUESTION = 4
MAX_TOTAL = NUM_QUESTIONS * MAX_PER_QUESTION

PROMPT_TEMPLATE = """Оцени ТОЛЬКО один вопрос по тексту ниже (за последние 2 недели).

Вопрос: «{question}»

Учитывай, что люди часто преуменьшают проблемы, поэтому слегка корректируй в сторону повышения, но НЕ ЗАВЫШАЙ без причины.

Примеры (учись на них):
Текст: "в целом нормально, иногда устаю, сплю мало
-> 2 балла

Текст: постоянно раздражаюсь, всё бесит пару дней в неделю
-> 3 балла

Текст: каждый день злость, хочу всех убить
-> 4 балла

Текст: вообще не упомянуто
-> 0 или 1

Шкала:
0 - никогда
1 - почти никогда
2 - иногда
3 - часто
4 - очень часто

Выводи ТОЛЬКО одно число.

Текст пользователя:
{history}

Ответ:"""

def call_model_single(history: str, question: str) -> int:
    prompt = PROMPT_TEMPLATE.format(history=history, question=question)
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.42,
                "top_p": 0.92,
                "top_k": 35,
                "min_p": 0.07,
                "repeat_penalty": 1.08
            }
        }, timeout=60)
        resp.raise_for_status()
        text = resp.json()["response"].strip()
        match = re.search(r'-?\d', text)
        return int(match.group()) if match else -1
    except Exception as e:
        print(f"Ошибка: {e}")
        return -1

async def main():
    print("Mireya - финальный анализ стресса (по твоим вопросам)")
    history = ""
    scores = [-2] * NUM_QUESTIONS  # -2 = ещё не оценивали

    while True:
        user_input = input("\nТекст или ответ на вопрос (/end - выйти): ")
        if user_input.lower() == "/end":
            break
        history += "\n" + user_input

        need_clarify = []
        for i in range(NUM_QUESTIONS):
            if scores[i] == -2 or scores[i] == -1:
                score = call_model_single(history, QUESTIONS[i])
                scores[i] = score
                print(f"Вопрос {i+1}: {score} баллов")
                if score == -1:
                    need_clarify.append(i+1)

        if need_clarify:
            print("\nОтветь подробнее на эти вопросы (можно в одном сообщении):")
            for i in need_clarify:
                print(f"{i}. {QUESTIONS[i-1]}")
            continue

        # Всё закрыто - считаем процент
        total = sum(scores)
        stress_percent = round((total / MAX_TOTAL) * 100, 1)

        print("\n" + "="*50)
        print("АНАЛИЗ ЗАВЕРШЁН")
        print("="*50)
        for i, score in enumerate(scores, 1):
            print(f"{i:2}. {score} баллов")
        print("-"*50)
        print(f"Сумма баллов: {total}/{MAX_TOTAL}")
        print(f"УРОВЕНЬ СТРЕССА: {stress_percent}%")
        print("="*50)

        if stress_percent >= 85:
            print("Ты в зоне критического стресса. Это серьёзно.")
        elif stress_percent >= 65:
            print("Высокий стресс. Стоит обратить внимание.")
        elif stress_percent >= 40:
            print("Средний уровень стресса.")
        else:
            print("Стресс в норме.")
        break

if __name__ == "__main__":
    asyncio.run(main())