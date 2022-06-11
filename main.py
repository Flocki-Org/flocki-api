import uvicorn
from fastapi import FastAPI
from src.app.database import engine, SessionLocal
from src.app.people.models.database import models
from src.app.people.routers import person

models.Base.metadata.create_all(engine)

people = {}
app = FastAPI()
app.include_router(person.router)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api.'

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)