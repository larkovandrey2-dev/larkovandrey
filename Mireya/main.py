import time
#методы с БД, запросы на нейронку
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, HTMLResponse
from Mireya.database_scripts import get_users_id, add_gad7_answer
from supabase import create_client, Client
import os
from dotenv import load_dotenv
# initialize database
load_dotenv()
SUPABASE_URL = supabase_url = os.getenv('SUPABASE_URL')
SUPABASE_KEY  = supabase_url = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = supabase_url = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

people = []
app = FastAPI()
class User():
    def __init__(self, id, data=None):
        self.id = id
        self.data = []
@app.get("/")
def root():
    html_content = "<h2>Hello Mireya<h2>"
    return HTMLResponse(content=html_content)

@app.get("/api/register_user/{id}")
def register_user(id):
    if id not in get_users_id(people):
        people.append(User(id))
    return people
@app.get("/api/add_answer/{id}/{question_n}&{text}&{date}")
def add_answer(id,questionnaire_n, question_n,text,date):
    add_gad7_answer(id,questionnaire_n,question_n,text,date)
    for person in people:
        if person.id == id:
            person.data.append({'question_n': question_n, 'text': text, 'date': date})
            return person.data
    return JSONResponse({"error": "No such user"})
@app.get("/api/get_user/{id}")
def get_user(id):
    for i in people:
        if i.id == id:
            return {'id': i.id, 'data': i.data}
    return JSONResponse({"error": "User not found"}, status_code=404)
@app.get("/api/show_all_users")
def show_all_users():
    res = []
    for person in people:
        res.append({'id': person.id, 'data': person.data})
    return res
