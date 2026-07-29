from fastapi import FastAPI
from app.schemas.chat import Request, Response

app = FastAPI()

@app.post("/v1/chat/completions")
def chat_completions(request: Request):
    return {"message": "not implemented yet"}