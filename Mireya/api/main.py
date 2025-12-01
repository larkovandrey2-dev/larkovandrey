import os
import random
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from llm_service import interaction as llm
from helpers.database import DatabaseService
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY not found.")
db = DatabaseService(SUPABASE_URL, SUPABASE_SERVICE_KEY)



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
class QuestionOut(BaseModel):
    question_index: int
    survey_index: int
class ResultIn(BaseModel):
    user_id: int
    global_n: int
    survey_n: int
    date: str
    result: int

class LLMRequest(BaseModel):
    question: str
    question_n: int
    answer: str
    last_json: dict
    attempt: int = 0
class RephraseQuestion(BaseModel):
    question: str = "Как ты себя чувствуешь?"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_client()
    print("Supabase initialized")
    yield
app = FastAPI(title="Mireya API", version="1.1", lifespan=lifespan)


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
@app.get("/api/all_users")
async def get_all_users():
    try:
        users = await db.get_all_users()
        return {"status": "ok", "users": users}
    except Exception as e:
        logging.error(e)
        return {"status": "error", "message": str(e)}

@app.post("/api/add_answer")
async def add_answer(data: AnswerIn):
    """Новый POST добавления ответа."""
    try:
        
        await db.add_user_answer(data.user_id, data.global_n,data.survey_n, data.question_n, data.text, data.date)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error in add_answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/add_survey_result")
async def add_survey_result(data: ResultIn):
    try:
        await db.add_survey_result(data.user_id, data.global_n, data.survey_n, data.date, data.result)
        user_stats = await db.get_user_stats(data.user_id)
        surveys_user_c = user_stats.get('surveys_count', 0) or 0
        results_list = user_stats.get('all_user_global_attempts') or []
        if data.global_n not in results_list:
            results_list.append(data.global_n)
        
        await db.change_user_stat(data.user_id, 'last_survey_index', data.survey_n)
        await db.change_user_stat(data.user_id, 'surveys_count', surveys_user_c + 1)
        await db.change_user_stat(data.user_id, 'all_user_global_attempts', results_list)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error in add_survey_result: {e}")
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
    try:
        users = await db.get_all_users()
        import asyncio
        stats_tasks = [db.get_user_stats(u) for u in users]
        stats_list = await asyncio.gather(*stats_tasks, return_exceptions=True)
        result = [s for s in stats_list if isinstance(s, dict)]
        return result
    except Exception as e:
        logging.error(f"Error in show_all_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
        global_n = await get_global_number()
        return {"data": filtered, "global_n": global_n}
    except Exception as e:
        logging.error(f"Error in get_questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_all_questions")
async def get_all_questions():
    try:
        questions = await db.all_questions()
        return {"data": questions, "questions": questions}
    except Exception as e:
        logging.error(f"Error in get_all_questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete_question")
async def delete_question(data: QuestionOut):
    try:
        await db.delete_question(data.question_index,data.survey_index)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error in delete_question: {e}")
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
        global_n = await get_global_number()
        return {"questions": selected, "global_n": global_n}
    except Exception as e:
        logging.error(f"Error in get_question_list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_llm(data: LLMRequest):
    try:
        llm_response = await llm.analyze_question(
            data.question,
            data.question_n,
            data.answer,
            data.last_json,
            data.attempt
        )
        return {"status": "ok", "llm_response": llm_response}
    except Exception as e:
        logging.error(f"Error in generate_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/rephrase_question")
async def rephrase_question(data: RephraseQuestion):
    try:
        llm_response = await llm.diversify_question(
            data.question)
        return {"status": "ok", "llm_response": llm_response}
    except Exception as e:
        logging.error(f"Error in generate_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


async def get_global_number():
    global_surveys_n = list(set(await db.all_global_attempts()))
    global_surveys_n.sort()
    if not global_surveys_n:
        global_surveys_n = [0]
    new_global_number = global_surveys_n[-1] + 1
    return new_global_number