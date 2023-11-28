from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
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


url = URL.create(
  drivername="mysql+pymysql",
  username="rokas",
  password=get_password(),
  host="localhost",
  database="movies",
  port=3306
)

engine = create_engine(url)
Session = sessionmaker(bind=engine)
sql = Session()

Base = declarative_base()
