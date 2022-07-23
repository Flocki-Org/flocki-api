import uvicorn
import os
from fastapi import FastAPI
from sqlalchemy import func

from src.app.database import engine, SessionLocal
from src.app.users.models.database import models
from src.app.people.routers import person, household
from src.app.users.models.database.models import User
from src.app.users.routers import user, login
from src.app.users.services.userFactory import hash_pwd
from src.app.config import settings

models.Base.metadata.create_all(engine)

people = {}
app = FastAPI()
app.include_router(person.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(household.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This sets up an initial user and is here only for now in the early stages of devs. Will move to migrations when ready.
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    user = db.query(models.User).filter(func.lower(models.User.email) == "admin@flocki.org").first()

    if not user:
        new_user = User(
            first_name="admin",
            last_name="admin",
            email="admin@flocki.org",
            mobile_number="+27000000000",
            password=hash_pwd("f10ck1.0rg"))

        db.add(new_user)
        db.commit()

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api.'

if __name__ == "__main__":
    print(f"Listening on port {os.environ.get('PORT')}")
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=int(os.environ.get('PORT', settings.flocki_app_port)))