from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MovieMovieMovie"
    db_dev: str
    db_prod: str
    dev: bool

    class Config:
        env_file = ".env"
