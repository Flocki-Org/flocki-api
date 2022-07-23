from ..models.database.models import PeopleAddress
from ...people.models.person import Person, SocialMediaLink, Address
from ...people.models.database import models

def createPersonFromPersonEntity(person_entity):
    person_response = Person(
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
            address_response = Address(
                id=address.id,
                type=address.type,
                streetNumber=address.streetNumber,
                street=address.street,
                suburb=address.suburb,
                city=address.city,
                province=address.province,
                country=address.country,
                postalCode=address.postalCode,
                latitude=address.latitude,
                longitude=address.longitude)

            person_response.addresses.append(address_response)

    return person_response


def createPersonEntityFromPerson(person):
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
    )
    if person.social_media_links:
        for sml in person.social_media_links:
            new_sml = models.SocialMediaLink(type=sml.type, url=sml.url)
            new_person.social_media_links.append(new_sml)

    if person.addresses:
        #TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
        # multiple rows in the DB for the same address
        for address in person.addresses:
            new_address = models.Address(
                type=address.type,
                streetNumber=address.streetNumber,
                street=address.street,
                suburb=address.suburb,
                city=address.city,
                province=address.province,
                country=address.country,
                postalCode=address.postalCode,
                latitude=address.latitude,
                longitude=address.longitude)

            pa = models.PeopleAddress(
                address = new_address,
                person = new_person
            )
            new_person.addresses.append(pa)

    return new_person
