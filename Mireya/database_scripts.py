from supabase import create_client, Client
import supabase
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY  = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
#Добавить функцию изменения статов пользователя, чтобы и последний номер опроса можно было менять и количество пройденных опросов
#Добавить строки пол, возраст, образование в пользователи, таблица вопросов:текст вопроса, принадлежность к опросу(1,2,...). Метод изменения вопросов и их добавления
def all_users() -> list:
    response = supabase.table("users").select("user_id").execute()
    users = [item["user_id"] for item in response.data]
    return users

def create_user(id :int, last_survey_index: int, role = "user", refer_id = 0):
    try:
        if id in all_users():
            print("User already exists")
        else:
            new_user = {
                "user_id": id,
                "role": role,
                "refer_id": refer_id,
                "last_survey_index": last_survey_index # default None
            }
            response = supabase.table('users').insert(new_user).execute()
            if response:
                print("User added")
    except Exception as e:
        print(f"Error in create_user: {e}")

def get_user_stats(id: int) -> dict:
    try:
        id = int(id)
        if id not in all_users():
            print("No such user, creating...")
            create_user(id)
        response = supabase.table("users").select("role, refer_id, surveys_count, last_survey_index").eq("user_id", id).execute()
        user_data = response.data[0]
        return user_data
    except Exception as e:
        print(f"Error in get_user_stats: {e}")

def add_gad7_answer(user_id: int, survey_index: int, question_index: int, response_text: str, response_date: str):
    try:
        new_response = {
            "user_id": int(user_id),
            "survey_index": int(survey_index),
            "question_index": int(question_index),
            "response_text": str(response_text),
            "response_date": str(response_date)
        }
        response = supabase.table("user_gad7_responses").insert(new_response).execute()
    except Exception as e:
        print(f"Error in add_gad7_answer: {e}")