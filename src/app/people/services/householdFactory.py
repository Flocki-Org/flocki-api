from typing import List

from .peopleFactory import PeopleFactory
from ...database import SessionLocal
from ...people.models.household import Household, CreateHousehold
from ...people.models.database import models
from ...people.models.people import Address

class HouseholdFactory:
    peopleFactory = PeopleFactory()
    def createHouseholdFromHouseholdEntity(self, household_entity: models.Household):

        leader_response = None
        if household_entity.leader:
            leader_response = self.peopleFactory.createPersonFromPersonEntity(household_entity.leader)

        address_response = Address(
            id=household_entity.address.id,
            type=household_entity.address.type,
            streetNumber=household_entity.address.streetNumber,
            street=household_entity.address.street,
            suburb=household_entity.address.suburb,
            city=household_entity.address.city,
            province=household_entity.address.province,
            country=household_entity.address.country,
            postalCode=household_entity.address.postalCode,
            latitude=household_entity.address.latitude,
            longitude=household_entity.address.longitude)

        people = []
        if household_entity.people:
            for person in household_entity.people:
                person_response = self.peopleFactory.createPersonFromPersonEntity(person, False)
                people.append(person_response)

        household_response = Household(
            id=household_entity.id,
            leader=leader_response,
            address=address_response,
            people = people
        )
        return household_response

    def createHouseholdEntityFromHousehold(self, household: CreateHousehold, people_models: List[models.Person]):
        new_household = models.Household(
            leader_id=household.leader.id,
            address_id=household.address_id,
            people=people_models
        )
        return new_household
