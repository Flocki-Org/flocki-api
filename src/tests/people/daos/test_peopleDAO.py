from datetime import datetime
from time import strptime

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
peopleDAO = PeopleDAO(db)

def test_get_all():
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
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    person = peopleDAO.get_person_by_id(-1)
    assert person is None

def test_update_person():
    # test update person
    # update_person(self, person_id, update_values, image_entity=None):
    existing_person = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number = "0721231234",
        #date_of_birth = "1984-10-01",
        gender = "male",
        #marriage_date = "2015-10-01",
        marital_status = "single",
        #egistered_date = "2020-01-01"
    )
    print("got here")
    db.add(existing_person)
    db.commit()
    db.refresh(existing_person)
    peopleDAO.update_person(existing_person.id, {
        "first_name": "Test Name Updated",
        "last_name": "Last Name Updated",
        "email": "test_updated@test.com",
        "mobile_number": "0721231235",
        "gender": "female",
        "marital_status": "married",
        "marriage_date":  datetime(2020, 1, 1, 0 ,0),
        "registered_date": datetime(2022, 1, 1, 10, 10, 10),
        "date_of_birth": datetime(1984, 1, 1, 10, 10, 10),

    }, None)
    updated_person = db.query(models.Person).filter(models.Person.id == existing_person.id).first()
    assert updated_person.first_name == "Test Name Updated"
    assert updated_person.last_name == "Last Name Updated"
    assert updated_person.email == "test_updated@test.com"
    assert updated_person.mobile_number == "0721231235"
    assert updated_person.gender == "female"
    assert updated_person.marital_status == "married"
    assert updated_person.marriage_date == datetime(2020, 1, 1).date()
    assert updated_person.registered_date == datetime(2022, 1, 1, 0, 0).date()
    assert updated_person.date_of_birth == datetime(1984, 1, 1, 0, 0).date()
