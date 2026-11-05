from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.church.daos.churchDAO import ChurchDAO
from src.app.church.models.database import models
from src.app.media.models.database import models as media_models  # noqa: F401
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.worship.models.database import models as worship_models  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_church_dao.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


db = next(override_get_db())
church_dao = ChurchDAO(db)


def test_create_and_get_church(test_db):
    church = church_dao.create_church(
        models.Church(name="Flocki Church", created=datetime.now(), email="info@flocki.org")
    )

    fetched = church_dao.get_church()
    assert fetched.id == church.id
    assert fetched.name == "Flocki Church"


def test_create_church_rejects_second_church(test_db):
    church_dao.create_church(models.Church(name="One", created=datetime.now()))
    with pytest.raises(Exception, match="Church already exists"):
        church_dao.create_church(models.Church(name="Two", created=datetime.now()))


def test_update_church(test_db):
    church_dao.create_church(models.Church(name="Old", created=datetime.now(), phone="111"))
    updated = church_dao.update_church({"name": "New", "phone": "222"})

    assert updated.name == "New"
    assert updated.phone == "222"


def test_delete_church(test_db):
    church_dao.create_church(models.Church(name="Temp", created=datetime.now()))
    church_dao.delete_church()
    assert church_dao.get_church() is None


def test_delete_church_when_missing(test_db):
    with pytest.raises(Exception, match="no existing church"):
        church_dao.delete_church()
