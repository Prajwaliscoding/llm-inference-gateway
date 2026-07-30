from fastapi import FastAPI, HTTPException
from app.schemas.chat import Request, Response
import httpx

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", 
                                        json = request.model_dump(), 
                                        headers = {"Authorization": "Bearer OPENAI_API_KEY"})

    except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to reach OpenAI")
    if response.status_code >= 500:
            raise HTTPException(status_code=502, detail="OpenAI server failed")
    return response.json()

    