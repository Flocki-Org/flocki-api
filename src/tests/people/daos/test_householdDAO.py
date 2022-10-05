import pytest

from src.app.database import get_db, SessionLocal, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.media.models.database import models as media_models

from src.app.people.models.database import models
# test_database.py
from src.app.people.daos.householdDAO import HouseholdDAO

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
    Base.metadata.drop_all(bind=engine)

db = next(override_get_db())
householdDAO = HouseholdDAO(db)


def test_get_all_households_no_households(test_db):
    households = householdDAO.get_all_households()
    len(households) == 0


def test_get_all_households_one_household(test_db):
    household = models.Household(
        leader_id=1,
        address_id=1,
    )
    db.add(household)
    db.commit()
    households = householdDAO.get_all_households()
    assert len(households) == 1


def test_get_all_households_many_households(test_db):
    household =  models.Household(
        leader_id=1,
        address_id=1,
    )
    household_2 =  models.Household(
        leader_id=1,
        address_id=1,
    )
    db.add(household)
    db.add(household_2)
    db.commit()
    households = householdDAO.get_all_households()
    assert len(households) == 2


