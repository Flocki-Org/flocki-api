from typing import List

from fastapi import Depends

from .peopleFactory import PeopleFactory
from ...media.factories.mediaFactory import MediaFactory
from ...media.models.media import DisplayImage
from ...people.models.household import Household, CreateHousehold
from ...people.models.database import models
from ...people.models.people import Address

class HouseholdFactory:
    def __init__(self, people_factory: PeopleFactory = Depends(PeopleFactory), media_factory: MediaFactory = Depends(MediaFactory)):
        self.people_factory = people_factory
        self.media_factory = media_factory

    def createHouseholdFromHouseholdEntity(self, household_entity: models.Household, include_household_image=False):

        leader_response = None
        if household_entity.leader:
            leader_response = self.people_factory.createPersonFromPersonEntity(household_entity.leader)

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
                person_response = self.people_factory.createPersonFromPersonEntity(person, False)
                people.append(person_response)

        household_response = Household(
            id=household_entity.id,
            leader=leader_response,
            address=address_response,
            people = people
        )

        if include_household_image and household_entity.household_images:
            images = sorted(household_entity.household_images, key=lambda x: x.id, reverse=True)
            if len(images) > 0 and images[0] is not None:
                household_response.household_image = self.media_factory.createImageFromImageEntity(images[0].image)

        return household_response

    def createHouseholdEntityFromHousehold(self, household: CreateHousehold, people_models: List[models.Person]):
        new_household = models.Household(
            leader_id=household.leader.id,
            address_id=household.address.id,
            people=people_models
        )
        return new_household

    def create_household_image_list_from_entity_list(self, household_entity: models.Household):
        images = sorted(household_entity.household_images, key=lambda x: x.id, reverse=True)
        household_image_list: List[DisplayImage] = []
        for image in images:
            household_image_list.append(self.media_factory.createImageFromImageEntity(image.image))
        return household_image_list

