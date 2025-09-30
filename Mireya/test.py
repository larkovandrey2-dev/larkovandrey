from supabase import create_client, Client
import os
from dotenv import load_dotenv
import asyncio 

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY  = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Асинхронный клиент
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

async def all_users() -> list:
    response = await supabase.table("users").select("user_id").execute()
    users = [item["user_id"] for item in response.data]
    return users

async def create_user(id: int, last_survey_index: int, role = "user", refer_id = 0):
    try:
        users_list = await all_users()  # await здесь!
        if id in users_list:
            print("User already exists")
        else:
            new_user = {
                "user_id": id,
                "role": role,
                "refer_id": refer_id,
                "last_survey_index": last_survey_index
            }
            response = await supabase.table('users').insert(new_user).execute()
            if response:
                print("User added")
    except Exception as e:
        print(f"Error in create_user: {e}")

async def get_user_stats(id: int) -> dict:
    try:
        id = int(id)
        users_list = await all_users()  # await здесь!
        if id not in users_list:
            print("No such user, creating...")
            await create_user(id, 0)  # await здесь!
        response = await supabase.table("users").select("role, refer_id, surveys_count").eq("user_id", id).execute()
        user_data = response.data[0]
        return user_data
    except Exception as e:
        print(f"Error in get_user_stats: {e}")

async def add_gad7_answer(user_id: int, survey_index: int, question_index: int, response_text: str, response_date: str):
    try:
        new_response = {
            "user_id": int(user_id),
            "survey_index": int(survey_index),
            "question_index": int(question_index),
            "response_text": str(response_text),
            "response_date": str(response_date)
        }
        response = await supabase.table("user_gad7_responses").insert(new_response).execute()
        print(f"Success: {response.data}")
        return response.data
    except Exception as e:
        print(f"Error in add_gad7_answer: {e}")
        return None

# Теперь работает с asyncio.run()
res = asyncio.run(add_gad7_answer(4, 4, 4, '4', '4'))
print(res)