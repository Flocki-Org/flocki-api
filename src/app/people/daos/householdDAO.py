from datetime import datetime

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from fastapi import Depends
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models
from src.app.people.models.database.models import HouseholdImage


class HouseholdDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db=db

    def get_all_households(self, params: Params = Params(page=1, size=100)) -> Page[models.Household]:
        return paginate(self.db.query(models.Household).order_by(models.Household.id), params)

    def get_household_by_id(self, id):
        return self.db.query(models.Household).filter(models.Household.id == id).first()

    def add_household(self, new_household, image_entity=None):
        self.db.add(new_household)
        self.db.commit()
        self.db.refresh(new_household)
        if image_entity is not None:
            self.add_household_image(new_household, image_entity)

        return self.get_household_by_id(new_household.id)

    def add_household_image(self, household_entity, image_entity):
        household_image = HouseholdImage(
            household=household_entity,
            image=image_entity,
            created=datetime.now(),
        )
        self.db.add(household_image)
        self.db.commit()

    def add_person_to_household(self, household_entity, person):
        household_entity.people.append(person)
        self.db.commit()

    def remove_person_from_household(self, household_entity, person):
        household_entity.people.remove(person)
        self.db.commit()

    def update_household(self, household_entity: models.Household, update_leader_id: int, update_address_id: int, image_entity=None):
        if image_entity is not None:
            household_image = HouseholdImage(
                household=household_entity,
                image=image_entity,
                created=datetime.now(),
            )
            self.db.add(household_image)
        household_entity.leader_id = update_leader_id
        household_entity.address_id = update_address_id
        self.db.commit()
