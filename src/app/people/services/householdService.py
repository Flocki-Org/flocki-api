from fastapi import Depends

from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.daos.householdDAO import HouseholdDAO

from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.household import CreateHousehold


class NoHouseholdException(Exception):
    pass

class HouseholdService:
    def __init__(self, household_DAO: HouseholdDAO = Depends(HouseholdDAO), household_factory: HouseholdFactory = Depends(HouseholdFactory), peopleDAO: PeopleDAO = Depends(PeopleDAO), people_factory: PeopleFactory = Depends(PeopleFactory)):
        self.people_DAO = peopleDAO
        self.people_factory = people_factory
        self.household_factory = household_factory
        self.household_DAO = household_DAO

    def get_all_households(self):
        households_response = []
        households = self.household_DAO.get_all_households()
        for household in households:
            households_response.append(self.household_factory.createHouseholdFromHouseholdEntity(household_entity=household))
        return households_response

    def get_household_by_id(self, id: int):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(f"Household does not exist with ID: {id}")
        return self.household_factory.createHouseholdFromHouseholdEntity(household_entity)

    def add_household(self, household: CreateHousehold):
        people_models = []
        for person in household.people:
            person_entity = self.people_DAO.get_person_by_id(person.id)
            if not person_entity:
                raise Exception(f"Person does not exist with ID: {person.id}")
            people_models.append(person_entity)

        new_household = self.household_factory.createHouseholdEntityFromHousehold(household, people_models)
        return self.household_factory.createHouseholdFromHouseholdEntity(self.household_DAO.add_household(new_household))
