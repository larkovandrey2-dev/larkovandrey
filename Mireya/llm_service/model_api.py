from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
import uvicorn

app = FastAPI()

# Инициализация модели
llm = Llama(model_path="llm_service", n_ctx=1024, n_threads=4)

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
def generate(data: Prompt):
    words = data.prompt.split()
    if len(words) > 700:
        prompt_trimmed = " ".join(words[-700:])
    else:
        prompt_trimmed = data.prompt

    resp = llm(prompt_trimmed, max_tokens=256)
    return {"text": resp["choices"][0]["text"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
