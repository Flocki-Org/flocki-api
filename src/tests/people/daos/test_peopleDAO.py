from main import app
from src.app.database import get_db, SessionLocal
from src.app.people.daos.peopleDAO import PeopleDAO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# test_database.py
from src.app.people.models.database import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(engine)

def override_get_db():
    connection = engine.connect()

    # begin a non-ORM transaction
    transaction = connection.begin()

    # bind an individual Session to the connection
    db = SessionLocal(bind=connection)
    # db = Session(engine)

    yield db

    db.rollback()
    connection.close()



app.dependency_overrides[get_db] = override_get_db
db = next(override_get_db())

def test_get_all():
    peopleDAO = PeopleDAO(db)
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    new_person_2 = models.Person(
        first_name="Test Name 2"
    )
    db.add(new_person_1)
    db.add(new_person_2)
    db.commit()
    people = peopleDAO.get_all()
    assert len(people) == 2
    assert people[0].first_name == new_person_1.first_name
    assert people[1].first_name == new_person_2.first_name


def test_get_person_by_id_person_found():
    # test get_person_by_id
    peopleDAO = PeopleDAO(db)
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    person = peopleDAO.get_person_by_id(new_person_1.id)
    assert person.id == new_person_1.id
    assert person.first_name == new_person_1.first_name


def test_get_person_by_id_person_not_found():
    # test get_person_by_id
    peopleDAO = PeopleDAO(db)
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    person = peopleDAO.get_person_by_id(-1)
    assert person is None
