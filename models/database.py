from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "mysql+pymysql://root:bananas@localhost:3306/movies"
DATABASE_URL = "mysql+pymysql://root:N3zinau!@localhost:3306/movies"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
sql = SessionLocal()
Base = declarative_base()
