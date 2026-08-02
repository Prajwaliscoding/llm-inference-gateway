from fastapi import FastAPI, HTTPException, Depends
from app.schemas.chat import Request, Response
import httpx
from app.config import settings
from app.auth import verify_token
from app.logging_config import configure_logging, logger
import uuid
from app.providers.factory import get_provider

configure_logging()

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request, call_next):
      request_id = str(uuid.uuid4())
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
async def chat_completions(request: Request) -> Response:
      provider = get_provider(request.model)
      response = await provider.chat_completion(request)
      return response



@app.get("/health")
async def health():
      return {"status":"okay"}