from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  ENV: str = "dev"
  POSTGRES_DB: str
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  POSTGRES_PORT: str

  DATABASE_URL: str
  SECRET_KEY: str

  class Config:
    env_file = ".env"

settings = Settings()