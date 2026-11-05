import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.media.models.database import models as media_models  # noqa: F401
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.models.database import models
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.worship.models.database import models as worship_models  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_address_dao.db"
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
address_dao = AddressDAO(db)


def test_create_and_get_address(test_db):
    created = address_dao.create_address(
        models.Address(
            type="home",
            street_number="21",
            street="Allan",
            suburb="Noordwyk",
            city="Midrand",
            province="GP",
            country="ZA",
            postal_code="1685",
        )
    )

    fetched = address_dao.get_address_by_id(created.id)
    assert fetched.street == "Allan"
    assert fetched.city == "Midrand"


def test_find_address(test_db):
    address_dao.create_address(
        models.Address(
            type="home",
            street_number="21",
            street="Allan",
            suburb="Noordwyk",
            city="Midrand",
            province="GP",
            country="ZA",
            postal_code="1685",
        )
    )

    found = address_dao.find_address("home", "21", "Allan", "Noordwyk", "Midrand", "GP", "ZA", "1685")
    assert found is not None
    assert address_dao.find_address("business", "21", "Allan", "Noordwyk", "Midrand", "GP", "ZA", "1685") is None


def test_update_address(test_db):
    created = address_dao.create_address(
        models.Address(type="home", street_number="1", street="Old", suburb="S", city="C", province="P", country="ZA")
    )
    address_dao.update_address(created.id, {"street": "New", "city": "Cape Town"})

    updated = address_dao.get_address_by_id(created.id)
    assert updated.street == "New"
    assert updated.city == "Cape Town"


def test_get_all_addresses_ordered(test_db):
    address_dao.create_address(
        models.Address(type="home", street_number="1", street="B Street", suburb="Z", city="B City", province="P", country="ZA")
    )
    address_dao.create_address(
        models.Address(type="home", street_number="2", street="A Street", suburb="A", city="A City", province="P", country="ZA")
    )

    addresses = address_dao.get_all_addresses()
    assert [a.city for a in addresses] == ["A City", "B City"]


def test_link_and_delete_person_address(test_db):
    person = models.Person(first_name="Joe", last_name="Soap", mobile_number="1")
    address = models.Address(type="home", street_number="1", street="Main", suburb="S", city="C", province="P", country="ZA")
    db.add(person)
    db.add(address)
    db.commit()
    db.refresh(person)
    db.refresh(address)

    address_dao.create_address_linked_to_person(address, person)
    db.commit()

    links = address_dao.get_existing_addresses_for_person(person.id)
    assert len(links) == 1
    address_dao.delete_address(links[0].id)
    db.commit()
    assert address_dao.get_existing_addresses_for_person(person.id) == []
