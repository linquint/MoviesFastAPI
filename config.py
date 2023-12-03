from pydantic import BaseSettings


class Settings(BaseSettings):
  app_name: str = "MovieMovieMovie"
  JWT_SECRET_KEY: str
  JWT_REFRESH_KEY: str

  class Config:
    env_file = ".env"
