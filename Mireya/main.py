import time



#методы с БД, запросы на нейронку

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, HTMLResponse

import CONFIG
from scripts import all_users,create_user,get_user_stats
from supabase import create_client, Client
from datetime import date
# initialize database
SUPABASE_URL = "https://gvwovsjkjeanyeyccyor.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2d292c2pramVhbnlleWNjeW9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5NjI2NjgsImV4cCI6MjA3MzUzODY2OH0.SzBKMxWfby2UNmVnSgvSjHwPISiXCFR3aQiRYBaZNgI"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2d292c2pramVhbnlleWNjeW9yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Nzk2MjY2OCwiZXhwIjoyMDczNTM4NjY4fQ.mPP7irVvx3TWjdLkw5O_0IpWd6FYHOcUvciqYkNzpQw"  # Из Settings → API
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
@app.get("/api/add_answer/{id}/{question_n}&{text}&{date}")
def add_answer(id,question_n,text,date):
    # create new database request
    new_question_response = {
        "user_id": id,
        "question_index": question_n,
        "response_text": str(text),
        "response_date": str(date)
    }
    response = supabase.table("user_responses").insert(new_question_response).execute()
    for person in people:
        if person.id == id:
            person.data.append({'question_n': question_n, 'text': text, 'date': date})
            return person.data
    return JSONResponse({"error": "No such user"})
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
