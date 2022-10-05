from datetime import datetime

# from main import app
import pytest

from src.app.database import get_db, SessionLocal, Base
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.media.models.database import models as media_models

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# test_database.py
from src.app.people.models.database import models
from src.app.people.models.database.models import Person, SocialMediaLink

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print("teardown of DB failed")
        print(e)


db = next(override_get_db())
peopleDAO = PeopleDAO(db)


def test_get_all(test_db):
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


def test_get_all_none(test_db):
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


def test_get_person_by_id_person_found(test_db):
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


def test_get_person_by_id_person_not_found(test_db):
    # test get_person_by_id
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    person = peopleDAO.get_person_by_id(-1)
    assert person is None


def test_update_person(test_db):
    # test update person
    # update_person(self, person_id, update_values, image_entity=None):
    existing_person = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        # date_of_birth = "1984-10-01",
        gender="male",
        # marriage_date = "2015-10-01",
        marital_status="single",
        # egistered_date = "2020-01-01"
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
        "marriage_date": datetime(2020, 1, 1, 0, 0),
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


def test_update_person_including_image(test_db):
    # test update person
    # update_person(self, person_id, update_values, image_entity=None):
    existing_person = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        # date_of_birth = "1984-10-01",
        gender="male",
        # marriage_date = "2015-10-01",
        marital_status="single",
        # egistered_date = "2020-01-01"
    )
    db.add(existing_person)
    db.commit()
    db.refresh(existing_person)

    image_entity = media_models.Image(
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )
    db.add(image_entity)
    db.commit()
    db.refresh(image_entity)

    peopleDAO.update_person(existing_person.id, {
        "first_name": "Test Name Updated",
        "last_name": "Last Name Updated",
        "email": "test_updated@test.com",
        "mobile_number": "0721231235",
        "gender": "female",
        "marital_status": "married",
        "marriage_date": datetime(2020, 1, 1, 0, 0),
        "registered_date": datetime(2022, 1, 1, 10, 10, 10),
        "date_of_birth": datetime(1984, 1, 1, 10, 10, 10),

    }, image_entity)
    updated_person: Person = db.query(models.Person).filter(models.Person.id == existing_person.id).first()

    assert updated_person.first_name == "Test Name Updated"
    assert updated_person.last_name == "Last Name Updated"
    assert updated_person.email == "test_updated@test.com"
    assert updated_person.mobile_number == "0721231235"
    assert updated_person.gender == "female"
    assert updated_person.marital_status == "married"
    assert updated_person.marriage_date == datetime(2020, 1, 1).date()
    assert updated_person.registered_date == datetime(2022, 1, 1, 0, 0).date()
    assert updated_person.date_of_birth == datetime(1984, 1, 1, 0, 0).date()
    assert updated_person.profile_images[0].id == image_entity.id


def test_get_existing_social_media_links(test_db):
    # test get_existing_social_media_links
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    sml_fb: SocialMediaLink = models.SocialMediaLink(
        person_id=new_person_1.id,
        type="facebook",
        url="https://www.facebook.com/test")

    sml_twitter: SocialMediaLink = models.SocialMediaLink(
        person_id=new_person_1.id,
        type="twitter",
        url="https://www.twitter.com/test")

    db.add(sml_fb)
    db.add(sml_twitter)
    db.commit()

    smls = peopleDAO.get_existing_social_media_links(new_person_1.id)
    assert len(smls) == 2
    assert smls[0].type == "facebook"
    assert smls[0].url == "https://www.facebook.com/test"
    assert smls[1].type == "twitter"
    assert smls[1].url == "https://www.twitter.com/test"


def test_delete_social_media_link(test_db):
    # test get_existing_social_media_links
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)
    sml_fb: SocialMediaLink = models.SocialMediaLink(
        person_id=new_person_1.id,
        type="facebook",
        url="https://www.facebook.com/test")

    sml_twitter: SocialMediaLink = models.SocialMediaLink(
        person_id=new_person_1.id,
        type="twitter",
        url="https://www.twitter.com/test")

    db.add(sml_fb)
    db.add(sml_twitter)
    db.commit()
    db.refresh(sml_fb)

    peopleDAO.delete_social_media_link(sml_fb.id)

    smls = db.query(models.SocialMediaLink).filter(
        models.SocialMediaLink.person_id == new_person_1.id).all()
    assert len(smls) == 1
    assert smls[0].type == "twitter"
    assert smls[0].url == "https://www.twitter.com/test"
    db.flush()
    db.commit()


def test_create_social_media_link(test_db):
    # test get_existing_social_media_links
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)

    peopleDAO.create_social_media_link(new_person_1.id, "facebook", "https://www.facebook.com/test")
    # TODO: this is a symptom of bad design....the create above should commit, but the reason it doesnt is because it
    #  is called before the person create, and should roll back if the create fails. However, it would be better to
    #  have one method in the DAO that rolls back everything.
    db.commit()
    smls = db.query(models.SocialMediaLink).filter(
        models.SocialMediaLink.person_id == new_person_1.id).all()
    assert len(smls) == 1
    assert smls[0].type == "facebook"
    assert smls[0].url == "https://www.facebook.com/test"


def test_create_person(test_db):
    new_person = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        # date_of_birth = "1984-10-01",
        gender="male",
        # marriage_date = "2015-10-01",
        marital_status="single",
        # egistered_date = "2020-01-01"
    )
    created_person = peopleDAO.create_person(new_person, None)

    assert created_person.id is not None
    assert created_person.first_name == "Test Name"
    assert created_person.last_name == "Last Name"
    assert created_person.email == "test@test.com"
    assert created_person.mobile_number == "0721231234"
    assert created_person.gender == "male"
    assert created_person.marital_status == "single"


def test_person_create_with_image(test_db):
    new_person = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        # date_of_birth = "1984-10-01",
        gender="male",
        # marriage_date = "2015-10-01",
        marital_status="single",
        # egistered_date = "2020-01-01"
    )

    new_image_entity = media_models.Image(
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )

    created_person: models.Person = peopleDAO.create_person(new_person, new_image_entity)

    assert created_person.id is not None
    assert created_person.first_name == "Test Name"
    assert created_person.last_name == "Last Name"
    assert created_person.email == "test@test.com"
    assert created_person.mobile_number == "0721231234"
    assert created_person.gender == "male"
    assert created_person.marital_status == "single"
    assert created_person.profile_images[0] is not None
    assert created_person.profile_images[0].image.address == "test_image.jpg"


def test_add_person_image(test_db):
    # test get_existing_social_media_links
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    db.add(new_person_1)
    db.commit()
    db.refresh(new_person_1)

    new_image_entity = media_models.Image(
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )

    peopleDAO.add_person_image(new_person_1, new_image_entity)

    person = db.query(models.Person).filter(models.Person.id == new_person_1.id).first()
    assert person.profile_images[0] is not None
    assert person.profile_images[0].image.address == "test_image.jpg"
