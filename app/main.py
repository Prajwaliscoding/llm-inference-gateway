from fastapi import FastAPI, Depends
from app.cache import build_cache_key, save_cache_value, find_cache_key
from app.schemas.chat import Request, Response
from app.config import settings
from app.auth import verify_token
from app.logging_config import configure_logging, logger
import uuid
from app.providers.factory import get_provider
from app.schemas.api_key import CreateApiKeyRequest, CreateApiKeyResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.security import generate_api_key, hash_api_key
from app.models.api_key import ApiKey
from app.auth import verify_admin
from app.rate_limit import check_rate_limit

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


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, api_key:ApiKey = Depends(verify_token)) -> Response:
      await check_rate_limit(api_key.id)

      cache_key = build_cache_key(request)
      find_in_cache = await find_cache_key(cache_key)
      if find_in_cache is not None:
            return Response(**find_in_cache)
      

      provider = get_provider(request.model)
      response = await provider.chat_completion(request)
      await save_cache_value(cache_key, response)
      return response



@app.get("/health")
async def health():
      return {"status":"okay"}



@app.post("/admin/keys", dependencies=[Depends(verify_admin)])
async def create_api_key(request:CreateApiKeyRequest, db:AsyncSession =Depends(get_db)):
      raw_key = generate_api_key()
      hashed = hash_api_key(raw_key)

      new_key = ApiKey(hashed_key = hashed, name = request.name)
      db.add(new_key)
      await db.commit()

      return CreateApiKeyResponse(id=new_key.id, name=new_key.name, api_key=raw_key)                         
