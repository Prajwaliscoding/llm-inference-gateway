from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    gateway_api_token: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    admin_token: str


    class Config:
        env_file = ".env"

settings = Settings() # type: ignore[call-arg]