from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config


@lru_cache()
def get_settings():
    return config.Settings()


@lru_cache()
def get_password():
    if get_settings().dev:
        return get_settings().db_dev
    return get_settings().db_prod


DATABASE_URL = f"mysql+pymysql://rokas:{get_password()}@localhost:3306/movies"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
sql = SessionLocal()
Base = declarative_base()
