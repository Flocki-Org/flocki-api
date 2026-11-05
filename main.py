import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.church.routers import church
from src.app.config import settings
from src.app.database import SessionLocal, init_db, running_on_render
from src.app.images.routers import image
from src.app.media.routers import media
from src.app.people.routers import address, household, person
from src.app.users.daos.userDAO import UserDAO
from src.app.users.factories.userFactory import UserFactory
from src.app.users.models.database.models import User
from src.app.users.routers import login, user
from src.app.users.services.passwordUtil import PasswordUtil
from src.app.users.services.userService import UserService
from src.app.worship.routers import song

# Ensure every SQLAlchemy model is registered on Base before init_db().
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.media.models.database import models as media_models  # noqa: F401
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.worship.models.database import models as worship_models  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flocki-api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_admin_user() -> None:
    # Early-dev convenience seed; replace with migrations when ready.
    user_DAO = UserDAO(db=next(get_db()))
    password_utils = PasswordUtil()
    user_factory = UserFactory(password_utils=password_utils)
    user_service = UserService(
        user_factory=user_factory,
        user_DAO=user_DAO,
        password_utils=password_utils,
    )
    if not user_service.get_user_by_name("admin@flocki.org"):
        user_service.create_user(
            User(
                first_name="admin",
                last_name="admin",
                email="admin@flocki.org",
                mobile_number="+27000000000",
                password=("f10ck1.0rg"),
            )
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_admin_user()
    logger.info("Startup complete")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(person.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(household.router)
app.include_router(media.router)
app.include_router(image.router)
app.include_router(address.router)
app.include_router(church.router)
app.include_router(song.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.flocki_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return "Hello this is the first endpoint of the flocki-api."


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.flocki_app_port))
    # reload breaks multi-worker / Render deploys; only use it for local dev.
    use_reload = not running_on_render() and os.environ.get("FLOCKI_RELOAD", "1") == "1"
    logger.info("Listening on port %s (reload=%s)", port, use_reload)
    uvicorn.run("main:app", host="0.0.0.0", reload=use_reload, port=port)
