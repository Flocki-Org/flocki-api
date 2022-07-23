from .peopleFactory import createPersonFromPersonEntity
from ...people.models.househould import Household
from ...people.models.database import models
from ...people.models.person import Address

def createHouseholdFromHouseholdEntity(household_entity: models.Household):

    leader_response = None
    if household_entity.leader:
        leader_response = createPersonFromPersonEntity(household_entity.leader)

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
            person_response = createPersonFromPersonEntity(person)
            people.append(person_response)

    household_response = Household(
        id=household_entity.id,
        leader=leader_response,
        address=address_response,
        people = people
    )


    return household_response
