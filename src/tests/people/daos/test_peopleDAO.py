from datetime import datetime
from unittest import mock

from fastapi_pagination import Params
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
from src.app.utils.DateUtils import DateUtils

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
    # setup test data
    new_person_1 = models.Person(
        first_name="Test Name"
    )
    new_person_2 = models.Person(
        first_name="Test Name 2"
    )
    db.add(new_person_1)
    db.add(new_person_2)
    db.commit()

    # method under test
    people_page = peopleDAO.get_all()

    # assertions
    people = people_page.items
    assert len(people) == 2
    assert people[0].first_name == new_person_1.first_name
    assert people[1].first_name == new_person_2.first_name


def test_get_all_pagination(test_db):
    new_person_1 = models.Person(
        first_name="A",
        last_name="B"
    )
    new_person_2 = models.Person(
        first_name="B",
        last_name="B"
    )
    db.add(new_person_1)
    db.add(new_person_2)
    db.commit()
    people_page = peopleDAO.get_all(Params(page=1, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].first_name == new_person_1.first_name

    people_page = peopleDAO.get_all(Params(page=2, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].first_name == new_person_2.first_name


def test_get_all_pagination_ordered_by_dob(test_db):
    new_person_1 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1984, 1, 1, 10, 10, 10),
    )
    new_person_2 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 1, 1, 10, 10, 10),
    )
    db.add(new_person_1)
    db.add(new_person_2)
    db.commit()
    people_page = peopleDAO.get_all(Params(page=1, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].date_of_birth == new_person_2.date_of_birth

    people_page = peopleDAO.get_all(Params(page=2, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].date_of_birth == new_person_1.date_of_birth


def test_get_all_pagination_ordered_by_id(test_db):
    new_person_1 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 1, 1, 10, 10, 10),
    )
    new_person_2 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 1, 1, 10, 10, 10),
    )
    db.add(new_person_1)
    db.add(new_person_2)
    db.commit()
    people_page = peopleDAO.get_all(Params(page=1, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].date_of_birth == new_person_1.date_of_birth

    people_page = peopleDAO.get_all(Params(page=2, size=1))
    people = people_page.items
    assert len(people) == 1
    assert people[0].date_of_birth == new_person_2.date_of_birth


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
    people_page = peopleDAO.get_all()
    people = people_page.items
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

    image_entity = media_models.MediaItem(
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

    new_image_entity = media_models.MediaItem(
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

    new_image_entity = media_models.MediaItem(
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )

    peopleDAO.add_person_image(new_person_1, new_image_entity)

    person = db.query(models.Person).filter(models.Person.id == new_person_1.id).first()
    assert person.profile_images[0] is not None
    assert person.profile_images[0].image.address == "test_image.jpg"


def test_find_people_by_email_or_first_name_and_last_name_match_email(test_db):
    match_by_email_1 = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="match@gmail.com")

    match_by_email_2 = models.Person(
        first_name="Test Name 2",
        last_name="Last Name 2",
        email="match@gmail.com")

    not_match_by_email = models.Person(
        first_name="Test Name 3",
        last_name="Last Name 3",
        email="not_match@gmail.com")

    db.add(match_by_email_1)
    db.add(match_by_email_2)
    db.add(not_match_by_email)
    db.commit()

    people = peopleDAO.find_people_by_email_or_first_name_and_last_name("match@gmail.com", "", "")

    assert len(people) == 2
    assert people[0].id == match_by_email_1.id
    assert people[0].first_name == "Test Name"
    assert people[1].id == match_by_email_2.id
    assert people[1].first_name == "Test Name 2"


def test_find_people_by_email_or_first_name_and_last_name_match_name(test_db):
    match_by_name_1 = models.Person(
        first_name="Match_First_1",
        last_name="Match_Last_1",
        email="non_match_email@gmail.com")

    match_by_name_2 = models.Person(
        first_name="Match_First_1",
        last_name="Match_Last_1",
        email="non_match_email_2@gmail.com")

    non_match_all = models.Person(
        first_name="Non_Match_First_2",
        last_name="Non_Match_Last_2",
        email="non_match_email@gmail.com")

    not_match_by_first_name = models.Person(
        first_name="Non_Match_First_1",
        last_name="Match_Last_1",
        email="non_match_email@gmail.com")

    not_match_by_last_name = models.Person(
        first_name="Match_First_1",
        last_name="Non_Match_Last_1",
        email="non_match_email@gmail.com")

    db.add(match_by_name_1)
    db.add(match_by_name_2)
    db.add(non_match_all)
    db.add(not_match_by_first_name)
    db.add(not_match_by_last_name)
    db.commit()

    people = peopleDAO.find_people_by_email_or_first_name_and_last_name("test@gmail.com", "Match_First_1",
                                                                        "Match_Last_1")

    assert len(people) == 2
    assert people[0].id == match_by_name_1.id
    assert people[0].first_name == "Match_First_1"
    assert people[1].id == match_by_name_2.id
    assert people[1].first_name == "Match_First_1"


def test_find_people_by_email_or_first_name_and_last_name_match_email_and_names(test_db):
    match_by_email_1 = models.Person(
        first_name="Test Name",
        last_name="Last Name",
        email="match@gmail.com")

    match_by_email_2 = models.Person(
        first_name="Test Name 2",
        last_name="Last Name 2",
        email="match@gmail.com")

    match_by_names = models.Person(
        first_name="Match_First",
        last_name="Match_Last",
        email="not_match@gmail.com")

    non_match = models.Person(
        first_name="Non Match First",
        last_name="Non Match Last",
        email="not_match@gmail.com")

    db.add(match_by_email_1)
    db.add(match_by_email_2)
    db.add(match_by_names)
    db.add(non_match)
    db.commit()

    people = peopleDAO.find_people_by_email_or_first_name_and_last_name("match@gmail.com", "Match_First", "Match_Last")

    # people is sorted by id, so should be in order of creation
    assert len(people) == 3
    assert people[0].id == match_by_email_1.id
    assert people[0].first_name == "Test Name"
    assert people[1].id == match_by_email_2.id
    assert people[1].first_name == "Test Name 2"
    assert people[2].id == match_by_names.id
    assert people[2].first_name == "Match_First"
    assert people[2].last_name == "Match_Last"


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_before_given_date_return_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 10, 25, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 11, 30, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_nov_15.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_before_given_date_next_month_return_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 11, 2, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 12, 2, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_nov_15.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_before_given_date_return_no_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 12, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 11, 30, 0, 0, 0))

    assert len(people) == 0


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_before_given_date_return_both_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 11, 30, 0, 0, 0))

    assert len(people) == 2
    assert people[0].id == new_person_jun_30.id
    assert people[1].id == new_person_nov_15.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_on_given_date_return_one_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 11, 15, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_nov_15.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_birthday_after_given_date_return_no_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2023, 11, 14, 0, 0, 0))

    assert len(people) == 0


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_all_people_with_birthday_before_date_in_the_following_year(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
    )

    new_person_jan_23 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1981, 1, 23, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.add(new_person_jan_23)
    db.commit()

    people = peopleDAO.find_people_with_birthday_before_given_date(datetime(2024, 2, 1, 0, 0, 0))

    assert len(people) == 2
    assert people[0].id == new_person_nov_15.id
    assert people[1].id == new_person_jan_23.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversary_before_given_date_return_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 10, 25, 0, 0, 0)

    new_person_dec_12 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 11, 15, 10, 10, 10),
        marriage_date=datetime(1980, 12, 10, 10, 10, 10),
    )
    new_person_jul_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 6, 30, 10, 10, 10),
        marriage_date=datetime(1980, 7, 15, 10, 10, 10),
    )
    db.add(new_person_dec_12)
    db.add(new_person_jul_15)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 12, 30, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_dec_12.id


@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversay_before_given_date_next_month_return_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 11, 2, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 1, 10, 10, 10, 10),
        marriage_date=datetime(1980, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        date_of_birth=datetime(1960, 10, 8, 10, 10, 10),
        marriage_date=datetime(1980, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 12, 2, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_nov_15.id


# #TODO change to correct test 2

@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversary_before_given_date_return_no_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 12, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 11, 30, 0, 0, 0))

    assert len(people) == 0


# #TODO change to correct test 3

@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversay_before_given_date_return_both_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 11, 15, 10, 10, 10),
    )
    new_person_jun_30 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 6, 30, 10, 10, 10),
    )
    db.add(new_person_nov_15)
    db.add(new_person_jun_30)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 11, 30, 0, 0, 0))

    assert len(people) == 2
    assert people[0].id == new_person_jun_30.id
    assert people[1].id == new_person_nov_15.id


# #TODO change to correct test 4

@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversary_on_given_date_return_one_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 11, 15, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 11, 15, 0, 0, 0))

    assert len(people) == 1
    assert people[0].id == new_person_nov_15.id


# #TODO change to correct test 5

@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_people_with_anniversary_after_given_date_return_no_result(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 11, 15, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2023, 11, 14, 0, 0, 0))

    assert len(people) == 0


# #TODO change to correct test 5

@mock.patch.object(DateUtils, 'get_current_datetime')
def test_find_all_people_with_anniversary_before_date_in_the_following_year(mock_get_current_datetime, test_db):
    mock_get_current_datetime.return_value = datetime(2023, 5, 1, 0, 0, 0)

    new_person_nov_15 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1960, 11, 15, 10, 10, 10),
    )

    new_person_jan_23 = models.Person(
        first_name="A",
        last_name="A",
        marriage_date=datetime(1981, 1, 23, 10, 10, 10),
    )

    db.add(new_person_nov_15)
    db.add(new_person_jan_23)
    db.commit()

    people = peopleDAO.find_people_with_anniversary_before_given_date(datetime(2024, 2, 1, 0, 0, 0))

    assert len(people) == 2
    assert people[0].id == new_person_nov_15.id
    assert people[1].id == new_person_jan_23.id
