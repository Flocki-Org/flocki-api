import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.database import engine, SessionLocal
from src.app.media.routers import media
from src.app.users.daos.userDAO import UserDAO
from src.app.users.models.database import models
from src.app.people.routers import person, household
from src.app.users.models.database.models import User
from src.app.users.routers import user, login
from src.app.users.factories.userFactory import UserFactory
from src.app.config import settings
from src.app.users.services.passwordUtil import PasswordUtil
from src.app.users.services.userService import UserService

models.Base.metadata.create_all(engine)

people = {}
app = FastAPI()
app.include_router(person.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(household.router)
app.include_router(media.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This sets up an initial user and is here only for now in the early stages of devs. Will move to migrations when ready.
@app.on_event("startup")
async def startup_event():
    user_DAO = UserDAO(db =  next(get_db()))
    password_utils = PasswordUtil()
    user_factory = UserFactory(password_utils=password_utils)
    user_service = UserService(user_factory=user_factory, user_DAO=user_DAO, password_utils=password_utils)
    if not user_service.get_user_by_name("admin@flocki.org"):
        user_service.create_user(User(
            first_name="admin",
            last_name="admin",
            email="admin@flocki.org",
            mobile_number="+27000000000",
            password=("f10ck1.0rg")))
    print("Startup event")

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api.'

if __name__ == "__main__":
    print(f"Listening on port {os.environ.get('PORT')}")
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=int(os.environ.get('PORT', settings.flocki_app_port)))