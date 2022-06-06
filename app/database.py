from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import os


SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.flocki_api_db_user_name}:{settings.flocki_api_db_password}@{settings.flocki_api_db_host}:{settings.flocki_api_db_port}/{settings.flocki_api_db_name}'
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()