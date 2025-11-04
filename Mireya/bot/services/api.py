import aiohttp
import logging

API_URL = "http://127.0.0.1:8000/api"


async def fetch_json(url: str, method: str = "GET", payload: dict | None = None):
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
    except aiohttp.ClientResponseError as e:
        logging.error(f"MireyaApi error {e.status}: {e.message}")
    except Exception as e:
        logging.error(f"Request failed: {e}")
    return None


async def register_user(user_id: int):
    url = f"{API_URL}/register_user/{user_id}"
    return await fetch_json(url)


async def get_user(user_id: int):
    url = f"{API_URL}/get_user/{user_id}"
    return await fetch_json(url)


async def get_all_users():
    url = f"{API_URL}/show_all_users"
    return await fetch_json(url)


async def add_answer(user_id: int, global_n: int, survey_n: int, question_n: int, text: str, date: str):
    url = f"{API_URL}/add_answer"
    payload = {
        "user_id": user_id,
        "global_n": global_n,
        "survey_n": survey_n,
        "question_n": question_n,
        "text": text,
        "date": date,
    }
    return await fetch_json(url, method="POST", payload=payload)


async def add_question(user_id: int, survey_n: int, question_n: int, text: str, global_n: int, date: str):
    url = f"{API_URL}/add_question"
    payload = {
        "user_id": user_id,
        "survey_n": survey_n,
        "question_n": question_n,
        "text": text,
        "global_n": global_n,
        "date": date,
    }
    return await fetch_json(url, method="POST", payload=payload)


async def get_questions(survey_id: int):
    url = f"{API_URL}/get_questions/{survey_id}"
    return await fetch_json(url)


async def get_question_list(user_id: int):
    url = f"{API_URL}/{user_id}/get_question_list"
    return await fetch_json(url)


