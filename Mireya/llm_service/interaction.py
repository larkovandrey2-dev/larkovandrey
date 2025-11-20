import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()
YC_API_TOKEN=os.getenv('YC_API_TOKEN')
MODEL_URI = "gpt://b1gcbn4fh3ils5usalqv/yandexgpt-5.1/latest"
HEADERS = {
    "Authorization": f"Bearer {YC_API_TOKEN}",
    "Content-Type": "application/json"
}

questions = [
    "Пользователь не мог заснуть после тяжёлого учебного дня или просыпался среди ночи не мог уснуть?",
    "Бывало ли такое, что тебе излишне долго не хотелось есть или наоборот ел всё подряд?",
    "Были ли у тебя резкие перепады настроения?",
    "Было ли такое, что ты не мог сдержать своё волнение?",
    "Было ли тебе тяжело усидеть на одном месте из-за постоянной нехватки времени?",
    "Есть ли у пользователя особенно сложные задания в учебе или вообще непонятные?",
    "Кажется ли тебе, что вокруг тебя одни гении?",
    "Есть ли у пользователя какие либо иные проблемы? (можно определять по эмоциональности речи)"
]

def ask_model(prompt: str) -> str:
    data = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "temperature": 0.0,
            "maxTokens": "80"
        },
        "messages": [
            {"role": "user", "text": prompt}
        ]
    }
    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers=HEADERS,
        data=json.dumps(data)
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Ошибка API: {response.status_code}, {response.text}")

async def analyze_question(question,question_n,answer,last_json=None) -> int | list:
    prompt = ("Прочитай ответ пользователя на вопрос и преобразуй его в числовую оценку по шкале: 'да' - 3, 'скорее да чем нет' - 2, 'скорее нет чем да' - 1, 'нет' - 0. Если ответ неочевиден, оцени исходя из контекста. Если данных явно недостаточно, верни -1. Ответ дай только числом."
              f"Вопрос: {question}. Ответ пользователя: {answer}")
    response = ask_model(prompt)['result']['alternatives'][0]['message']['text']
    print(response)
    if response != '-1' and response.isdecimal():
        last_json[question_n] = int(response)
    else:
        new_prompt = f"Тебе недостаточно данных для анализа, составь уточняющий вопрос к {question}. Верни мне только его текст абсолютно без лишних комментариев и пометок. Обязательно уложись в 65-75 символов на вопрос."
        new_response = ask_model(new_prompt)['result']['alternatives'][0]['message']['text']
        return [-1, new_response]
    return last_json





