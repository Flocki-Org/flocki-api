import pytest
from fastapi_pagination import Params
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.media.models.database import models as media_models  # noqa: F401
from src.app.users.daos.userDAO import UserDAO
from src.app.users.models.database import models
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.worship.models.database import models as worship_models  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user_dao.db"
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
user_dao = UserDAO(db)


def test_create_and_get_user_by_id(test_db):
    created = user_dao.create_user(
        models.User(
            first_name="Joe",
            last_name="Soap",
            email="joe@test.com",
            mobile_number="1",
            password="hashed",
        )
    )

    fetched = user_dao.get_user_by_id(created.id)
    assert fetched.email == "joe@test.com"
    assert fetched.first_name == "Joe"


def test_get_all_users_paginated(test_db):
    user_dao.create_user(models.User(first_name="A", last_name="A", email="a@test.com", mobile_number="1", password="x"))
    user_dao.create_user(models.User(first_name="B", last_name="B", email="b@test.com", mobile_number="2", password="x"))

    page = user_dao.get_all_users(Params(page=1, size=1))
    assert len(page.items) == 1
    assert page.total == 2


def test_get_user_by_name_is_case_insensitive(test_db):
    user_dao.create_user(
        models.User(first_name="Joe", last_name="Soap", email="Joe@Test.com", mobile_number="1", password="x")
    )

    found = user_dao.get_user_by_name("joe@test.com")
    assert found is not None
    assert found.email == "Joe@Test.com"


def test_get_user_by_name_missing(test_db):
    assert user_dao.get_user_by_name("missing@test.com") is None


def test_update_user(test_db):
    created = user_dao.create_user(
        models.User(first_name="Joe", last_name="Soap", email="joe@test.com", mobile_number="1", password="old")
    )

    user_dao.update_user(created.id, {"first_name": "Joseph", "password": "new", "id": 999})
    updated = user_dao.get_user_by_id(created.id)

    assert updated.first_name == "Joseph"
    assert updated.password == "new"
    assert updated.id == created.id


def test_update_user_person(test_db):
    person = people_models.Person(first_name="Ann", last_name="Lee", email="ann@test.com")
    db.add(person)
    db.commit()
    db.refresh(person)

    created = user_dao.create_user(
        models.User(first_name="Joe", last_name="Soap", email="joe@test.com", mobile_number="1", password="x")
    )
    user_dao.update_user_person(created.id, person.id)

    updated = user_dao.get_user_by_id(created.id)
    assert updated.person_id == person.id
