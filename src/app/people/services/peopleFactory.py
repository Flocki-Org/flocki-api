from ...people.models.person import Person, SocialMediaLink
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
            new_sml = models.SocialMediaLinks(type=sml.type, url=sml.url)
            new_person.social_media_links.append(new_sml)
    return new_person
