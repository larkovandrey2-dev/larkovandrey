import os
import random
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from bot.services.database import DatabaseService
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY not found.")
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)


app = FastAPI(title="Mireya API", version="1.1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

ADMINS = list(map(int, os.getenv("ADMINS", "").split(","))) if os.getenv("ADMINS") else []


class AnswerIn(BaseModel):
    user_id: int
    survey_n: int
    global_n: int
    question_n: int
    text: str = Field(..., max_length=500)
    date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class QuestionIn(BaseModel):
    user_id: int
    survey_n: int
    question_n: int
    text: str
    global_n: int
    date: str

@app.on_event("startup")
async def startup_event():
    await db.create_client()
    print("Supabase client initialized")

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h2>Hello Mireya</h2>"


@app.get("/api/register_user/{user_id}")
async def register_user(user_id: int):
    
    users = await db.get_all_users()
    if user_id not in users:
        role = "admin" if user_id in ADMINS else "user"
        await db.create_user(user_id, role, 0)
        logging.info(f"User {user_id} registered as {role}")
        return {"status": "created", "user_id": user_id, "role": role}
    return {"status": "exists", "user_id": user_id}

@app.post("/api/add_answer")
async def add_answer(data: AnswerIn):
    """Новый POST добавления ответа."""
    try:
        
        await db.add_user_answer(data.user_id, data.global_n,data.survey_n, data.question_n, data.text, data.date)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error in add_answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get_user/{user_id}")
async def get_user(user_id: int):
    try:
        
        stats = await db.get_user_stats(user_id)
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        return stats
    except Exception as e:
        logging.error(f"get_user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/show_all_users")
async def show_all_users():
    
    users = await db.get_all_users()
    result = []
    for u in users:
        stats = await db.get_user_stats(u)
        if stats:
            result.append(stats)
    return result



@app.post("/api/add_question")
async def add_question(data: QuestionIn):
    """Новый POST добавления вопроса."""
    try:
        
        await db.add_user_answer(
            data.user_id, data.global_n, data.survey_n, data.question_n, data.text, data.date
        )
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error in add_question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get_questions/{survey_id}")
async def get_questions(survey_id: int):
    try:
        
        questions = await db.all_questions()
        filtered = [q for q in questions if q["survey_index"] == survey_id]
        return {"data": filtered}
    except Exception as e:
        logging.error(f"Error in get_questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/{user_id}/get_question_list")
async def get_question_list(user_id: int):
    try:
        
        data = await db.get_user_stats(user_id)
        if not data:
            raise HTTPException(status_code=404, detail="User not found")

        last_survey_index = data.get("last_survey_index", -1)
        questions = await db.all_questions()

        survey_indices = list({q["survey_index"] for q in questions})
        if not survey_indices:
            raise HTTPException(status_code=404, detail="No surveys found")

        if len(survey_indices) == 1:
            survey_index = survey_indices[0]
        else:
            available = [i for i in survey_indices if i != last_survey_index]
            survey_index = random.choice(available) if available else survey_indices[0]

        selected = [q for q in questions if q["survey_index"] == survey_index]
        logging.info(f"User {user_id} got survey {survey_index}")
        return selected
    except Exception as e:
        logging.error(f"Error in get_question_list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
