from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings


# SQLAlchemy 2.1 treats postgresql:// as the psycopg 3 dialect. This app uses psycopg2.
SQLALCHEMY_DATABASE_URL = f'postgresql+psycopg2://{settings.flocki_api_db_user_name}:{settings.flocki_api_db_password}@{settings.flocki_api_db_host}:{settings.flocki_api_db_port}/{settings.flocki_api_db_name}'
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()