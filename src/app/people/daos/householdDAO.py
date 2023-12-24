from datetime import datetime
from typing import List

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from fastapi import Depends
from sqlalchemy import case, and_, or_

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

    def get_people_not_in_household(self, household_id):
        return self.db.query(models.Person).filter(
            ~models.Person.households.any(models.Household.id == household_id)).order_by(models.Person.last_name,
                                                                                        models.Person.first_name).all()


    def find_people_not_in_household_with_name_or_surname_starting_with(self, household_id, name, surname) -> List[models.Person]:
        # Create a case statement to calculate the sorting priority.
        surname_match = case(
            [
                (and_(models.Person.last_name.ilike(f"{surname}%"), models.Person.first_name.ilike(f"{name}%")),
                 1) if name and surname else (False, 1),
                (models.Person.last_name.ilike(f"{surname}%"), 2) if surname else (False, 2),
            ],
            else_=3
        )

        # Query and order the results based on the calculated priority.
        people_query = self.db.query(models.Person)

        if name and surname:
            people_query = people_query.filter(models.Person.first_name.ilike(f"{name}%"),
                                               models.Person.last_name.ilike(f"{surname}%"))
        elif name:
            people_query = people_query.filter(or_(models.Person.first_name.ilike(f"{name}%"), models.Person.last_name.ilike(f"{name}%")))
        elif surname:
            people_query = people_query.filter(models.Person.last_name.ilike(f"{surname}%"))

        people = people_query.order_by(surname_match, models.Person.last_name, models.Person.first_name).all()
        # remove people that are already in the household
        people = [person for person in people if household_id not in [household.id for household in person.households]]
        return people
