from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  ENV: str = "dev"
  POSTGRES_DB: str
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  POSTGRES_PORT: str

  DATABASE_URL: str
  SECRET_KEY: str
  CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

  class Config:
    env_file = ".env"

settings = Settings()