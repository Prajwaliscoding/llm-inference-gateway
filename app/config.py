from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    gateway_api_token: str


    class Config:
        env_file = ".env"

settings = Settings() # type: ignore[call-arg]