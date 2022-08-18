from typing import List

from fastapi import Depends

from ...media.models.media import ViewImage
from ...people.models.people import CreatePerson, SocialMediaLink, FullViewPerson
from ...people.factories.addressFactory import AddressFactory
from ...people.models.household import ViewHousehold
from ...people.models.database import models
from ...media.factories.mediaFactory import MediaFactory

class PeopleFactory:
    def __init__(self, address_factory: AddressFactory = Depends(AddressFactory), media_factory: MediaFactory = Depends(MediaFactory)):
        self.address_factory = address_factory
        self.media_factory = media_factory

    def createPersonFromPersonEntity(self, person_entity, include_household=True, include_profile_image=False):
        person_response = FullViewPerson(
            id=person_entity.id,
            first_name=person_entity.first_name,
            last_name=person_entity.last_name,
            email=person_entity.email,
            mobile_number=person_entity.mobile_number,
            date_of_birth=person_entity.date_of_birth,
            gender=person_entity.gender,
            marriage_date=person_entity.marriage_date,
            marital_status=person_entity.marital_status,
            registered_date=person_entity.registered_date,
        )
        if person_entity.social_media_links:
            for sml in person_entity.social_media_links:
                sml_response = SocialMediaLink(type=sml.type, url=sml.url)
                person_response.social_media_links.append(sml_response)

        if person_entity.addresses:
            for people_address in person_entity.addresses:
                address = people_address.address
                address_response = self.address_factory.create_address_from_address_entity(address)

                person_response.addresses.append(address_response)

        if include_household and person_entity.household:
            people = []
            for household_person in person_entity.household.people:
                person = self.createPersonFromPersonEntity(household_person, False)
                people.append(person)

            person_response.household = ViewHousehold(
                id=person_entity.household.id,
                leader=self.createPersonFromPersonEntity(person_entity.household.leader, False),
                address=self.address_factory.create_address_from_address_entity(person_entity.household.address),
                people=people
            )

        if include_profile_image and person_entity.profile_images:
            images = sorted(person_entity.profile_images, key=lambda x: x.id, reverse=True)
            if len(images) > 0 and images[0] is not None:
                person_response.profile_image = self.media_factory.createImageFromImageEntity(images[0].image)

        return person_response

    def create_profile_image_list_from_entity_list(self, person_entity):
        person_images = sorted(person_entity.profile_images, key=lambda x: x.id, reverse=True)
        profile_image_list: List[ViewImage] = []
        for person_image in person_images:
            profile_image_list.append(self.media_factory.createImageFromImageEntity(person_image.image))
        return profile_image_list

    def createPersonEntityFromPerson(self, person, address_entities=None):
        new_person = models.Person(
            first_name=person.first_name,
            last_name=person.last_name,
            email=person.email,
            mobile_number=person.mobile_number,
            date_of_birth=person.date_of_birth,
            gender=person.gender,
            marriage_date=person.marriage_date,
            marital_status=person.marital_status,
            registered_date=person.registered_date,
            household_id=person.household_id
        )
        if person.social_media_links:
            for sml in person.social_media_links:
                new_sml = models.SocialMediaLink(type=sml.type, url=sml.url)
                new_person.social_media_links.append(new_sml)

        if address_entities is not None:
            # TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
            # multiple rows in the DB for the same address
            for address_entity in address_entities:
                pa = models.PeopleAddress(
                    address=address_entity,
                    person=new_person
                )
                new_person.addresses.append(pa)

        return new_person
