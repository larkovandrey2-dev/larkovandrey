from supabase import create_client, Client
import supabase
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY  = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def all_users() -> list:
    '''returns a list with every user_id'''
    response = supabase.table("users").select("user_id").execute()
    users = [item["user_id"] for item in response.data]
    return users


def create_user(user_id :int, role: str, refer_id: int):
    '''create user'''
    try:
        if user_id in all_users():
            print("User already exists")
        else:
            new_user = {
                "user_id": user_id,
                "role": role,
                "refer_id": refer_id,
            }
            response = supabase.table('users').insert(new_user).execute()
            if response:
                print("User added")
    except Exception as e:
        print(f"Error in create_user: {e}")


def delete_user(user_id: int):
    '''delete user by user_id'''
    try:
        response = supabase.table("users").delete().eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error in delete_question: {e}")


def get_user_stats(user_id: int) -> dict:
    '''returns a dict of all stats'''
    try:
        user_id = int(user_id)
        if user_id not in all_users():
            print("No such user, creating...")
            create_user(user_id)
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        user_data = response.data[0]
        return user_data
    except Exception as e:
        print(f"Error in get_user_stats: {e}")


def change_user_stat(user_id: int, stat_name: str, new_value):
    '''change one specific stat by its name and its new value'''
    try:
        new_response = {f"{stat_name}": new_value}
        if user_id not in all_users():
            print(f"No such user_id for change_user_stat: {user_id}")
        else:
            response = supabase.table("users").update(new_response).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error in change_user_stat: {e}")


def change_user_stats(user_id: int, role: str, refer_id: int, surveys_count: int, last_survey_index: int, sex: str, age: int, education: str, all_user_global_attempts: list):
    '''change all stats for given user_id (function waits for every stat to be given)'''
    try:
        new_response = {
                    "role": role,
                    "refer_id": refer_id,
                    "last_survey_index": last_survey_index,
                    "surveys_count": surveys_count,
                    "sex": sex,
                    "age": age,
                    "education": education,
                    "all_user_global_attempts": all_user_global_attempts
                }
        if user_id not in all_users():
            print(f"No such user_id for change_user_stats: {user_id}")
        else:
            response = supabase.table("users").update(new_response).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error in change_user_stats: {e}")


def add_user_answer(user_id: int, attempt_global_index: int, survey_index: int, question_index: int, response_text: str, response_date: str):
    try:
        new_response = {
            "user_id": user_id,
            "survey_index": survey_index,
            "question_index": question_index,
            "response_text": response_text,
            "response_date": response_date,
            "attempt_global_index": attempt_global_index
        }
        response = supabase.table("user_responses").insert(new_response).execute()
    except Exception as e:
        print(f"Error in add_user_answer: {e}")


def all_questions():
    '''returns list of dicts: {'question_index':, 'survey_index':, 'question_text':}'''
    try:
        response = supabase.table("all_questions").select("question_index, survey_index, question_text").execute()
        return sorted(response.data, key=lambda x: (x['survey_index'],x['question_index']))
    except Exception as e:
        print(f"Error in all_questions: {e}")


def all_global_attempts():
    '''returns a list of all existing global attempts'''
    try:
        response = supabase.table("survey_results").select("attempt_global_index").execute()
        return [elem["attempt_global_index"] for elem in response.data]
    except Exception as e:
        print(f"Error in all_questions: {e}")


def add_question(question_index: int, survey_index: int, question_text: str):
    try:
        new_response = {
            "survey_index": int(survey_index),
            "question_index": int(question_index),
            "question_text": str(question_text)
        }

        if new_response in all_questions():
            print("This question exists")
        else:
            response = supabase.table("all_questions").insert(new_response).execute()
    except Exception as e:
        print(f"Error in add_gad7_answer: {e}")


def change_question(question_index: int, survey_index: int, new_question_text: str):
    '''change question text by its question_index and survey_index'''
    try:
        new_response = {"question_text": new_question_text}
        response = supabase.table("all_questions").update(new_response).eq("question_index", question_index).eq("survey_index", survey_index).execute()
    except Exception as e:
        print(f"Error in change_question: {e}")


def change_question_index(question_index: int, survey_index: int, new_question_index: int):
    '''change question index by its question_index and survey_index'''
    try:
        new_response = {"question_index": new_question_index}
        response = supabase.table('all_questions').update(new_response).eq("question_index", question_index).eq("survey_index", survey_index).execute()
    except Exception as e:
        print(f"Error in change_question_index: {e}")


def delete_question(question_index: int, survey_index: int):
    '''delete question by its question_index and survey_index'''
    try:
        response = supabase.table("all_questions").delete().eq("question_index", question_index).eq("survey_index", survey_index).execute()
    except Exception as e:
        print(f"Error in delete_question: {e}")


def add_survey_result(user_id: int, attempt_global_index: int, result: str):
    '''add a result for a single survey attempt'''
    try:
        new_response = {
            "user_id": user_id,
            "attempt_global_index": attempt_global_index,
            "result": result
        }
        if attempt_global_index in all_global_attempts():
            print(f"Global attempt with index {attempt_global_index} already exists")
        else:
            response = supabase.table("survey_results").insert(new_response).execute()
    except Exception as e:
        print(f"Error in add_survey_result: {e}")

