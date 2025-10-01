import time
#методы с БД, запросы на нейронку
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, HTMLResponse

import database_scripts
from database_scripts import all_users,create_user, get_user_stats, add_user_answer
from supabase import create_client, Client
import CONFIG
import os
import random
from dotenv import load_dotenv
# initialize database
load_dotenv()
SUPABASE_URL = supabase_url = os.getenv('SUPABASE_URL')
SUPABASE_KEY  = supabase_url = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = supabase_url = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
app = FastAPI()

@app.get("/")
def root():
    html_content = "<h2>Hello Mireya<h2>"
    return HTMLResponse(content=html_content)

@app.get("/api/register_user/{id}")
def register_user(id):
    if int(id) not in all_users():
        if int(id) in CONFIG.ADMINS:
            create_user(id, 'admin',0)
        else:
            create_user(id, 'user',0)

@app.get("/api/add_answer/{id}/{survey_n}&{question_n}&{text}&{date}")
def add_answer(id, survey_n,question_n,text,date):
    try:
        add_user_answer(id,survey_n,question_n,text,date)
    except Exception as e:
        print(f"Error in add_answer: {e}")

@app.get("/api/get_user/{id}")
def get_user(id):
    try:
        return get_user_stats(int(id))
    except Exception as e:
        print(e)
        return JSONResponse({"error": "User not found"}, status_code=404)
@app.get("/api/show_all_users")
def show_all_users():
    res = []
    for user in all_users():
        res.append(get_user_stats(user))
    return res
@app.get("/api/add_question/{user_id}&{survey_n}&{question_n}&{text}&{global_n}&{date}")
def add_question(user_id,survey_n,question_n,text,global_n,date):
    database_scripts.add_user_answer(user_id,global_n,survey_n,question_n,text,date)

@app.get("/api/get_questions/{survey_id}")
def get_question(survey_id):
    return JSONResponse({'data': [i for i in database_scripts.all_questions() if i['survey_index'] == int(survey_id)]})
@app.get("/api/{id}/get_question_list")
def get_question_list(id):
    try:
        data = get_user_stats(int(id))
        last_survey_index = data['last_survey_index']
        questions = database_scripts.all_questions()
        survey_index = random.choice(list(set(i['survey_index'] for i in questions)))
        while survey_index == last_survey_index and len(list(set(i['survey_index'] for i in questions))) > 1:
            survey_index = random.choice(list(set(i['survey_index'] for i in questions)))
        res = [i for i in questions if i['survey_index'] == survey_index]
        return res
    except Exception as e:
        print(e)