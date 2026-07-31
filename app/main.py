from fastapi import FastAPI, HTTPException, Depends
from app.schemas.chat import Request, Response
import httpx
from app.config import settings
from app.auth import verify_token
from app.logging_config import configure_logging, logger
import uuid

configure_logging()

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request, call_next):
      request_id = str(uuid.uuid4)
      logger.info("request received", request_id = request_id, path = request.url.path)

      try:
           response = await call_next(request)
      except Exception as e:
            logger.error("unhandled error", request_id = request_id, error = str(e))
            raise

      logger.info("response returned", request_id = request_id, status_code = response.status_code)

      response.headers["X-Request-ID"] = request_id

      return response


@app.post("/v1/chat/completions", dependencies = [Depends(verify_token)])
async def chat_completions(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            logger.info("provider called", provider ="openai")
            response = await client.post("https://api.openai.com/v1/chat/completions", 
                                        json = request.model_dump(), 
                                        headers = {"Authorization": f"Bearer {settings.openai_api_key}"})

    except httpx.RequestError:
            logger.error("provider unreachable", provider="openai")
            raise HTTPException(status_code=502, detail="Failed to reach OpenAI")
    if response.status_code >= 500:
            logger.error("provider server error", provider="openai", status_code=response.status_code)
            raise HTTPException(status_code=502, detail="OpenAI server failed")
    return response.json()

    