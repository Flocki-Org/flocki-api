from typing import List

from fastapi import Depends

from .peopleFactory import PeopleFactory
from ...media.factories.mediaFactory import MediaFactory
from ...media.models.media import ViewMediaItem
from ...people.models.household import ViewHousehold, CreateHousehold
from ...people.models.database import models
from ...people.models.people import ViewAddress


class HouseholdFactory:
    def __init__(self, people_factory: PeopleFactory = Depends(PeopleFactory), media_factory: MediaFactory = Depends(MediaFactory)):
        self.people_factory = people_factory
        self.media_factory = media_factory

    def createHouseholdFromHouseholdEntity(self, household_entity: models.Household, include_household_image=False) -> ViewHousehold:

        leader_response = None
        if household_entity.leader:
            leader_response = self.people_factory.create_person_from_person_entity(household_entity.leader)

        address_response = ViewAddress(
            id=household_entity.address.id,
            type=household_entity.address.type,
            street_number=household_entity.address.street_number,
            street=household_entity.address.street,
            suburb=household_entity.address.suburb,
            city=household_entity.address.city,
            province=household_entity.address.province,
            country=household_entity.address.country,
            postal_code=household_entity.address.postal_code,
            latitude=household_entity.address.latitude,
            longitude=household_entity.address.longitude)

        people = []
        if household_entity.people:
            for person in household_entity.people:
                person_response = self.people_factory.create_person_from_person_entity(person, include_households=False, include_profile_image=True)
                people.append(person_response)

        household_response = ViewHousehold(
            id=household_entity.id,
            leader=leader_response,
            address=address_response,
            people = people
        )

        if include_household_image and household_entity.household_images:
            images = sorted(household_entity.household_images, key=lambda x: x.id, reverse=True)
            if len(images) > 0 and images[0] is not None:
                household_response.household_image = self.media_factory.create_media_item_from_media_item_entity(images[0].image)

        return household_response

    def createHouseholdEntityFromHousehold(self, household: CreateHousehold, people_models: List[models.Person]):
        if household.leader_id is None and people_models is not None and len(people_models) > 0:
            household.leader_id = people_models[0].id

        new_household = models.Household(
            leader_id=household.leader_id,
            address_id=household.address_id,
        )
        for person in people_models:
            new_household.people.append(person)

        return new_household

    def create_household_image_list_from_entity_list(self, household_entity: models.Household):
        images = sorted(household_entity.household_images, key=lambda x: x.id, reverse=True)
        household_image_list: List[ViewMediaItem] = []
        for image in images:
            household_image_list.append(self.media_factory.create_media_item_from_media_item_entity(image.image))
        return household_image_list

