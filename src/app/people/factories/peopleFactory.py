from typing import List

from fastapi import Depends
from sqlalchemy import inspect as sa_inspect

from ...media.models.media import ViewMediaItem
from ...people.models.contacts import CategoryView, EmergencyContactView, PersonEmailView, PersonPhoneView, ServiceTypeView
from ...people.models.people import CreatePerson, SocialMediaLink, FullViewPerson, BasicViewPerson
from ...people.factories.addressFactory import AddressFactory
from ...people.models.household import ViewHousehold
from ...people.models.database import models
from ...media.factories.mediaFactory import MediaFactory
from ...people.personFields import PROFILE_PERSON_FIELDS
from ...users.models.user import DisplayUser


def _loaded(entity, name):
    try:
        state = sa_inspect(entity)
    except Exception:
        return []
    if name in getattr(state, "unloaded", set()):
        return []
    value = getattr(entity, name, None)
    return list(value or [])


class PeopleFactory:
    def __init__(self, address_factory: AddressFactory = Depends(AddressFactory), media_factory: MediaFactory = Depends(MediaFactory)):
        self.address_factory = address_factory
        self.media_factory = media_factory


    def create_basic_person_view_from_person_entity(self, person_entity, include_profile_image=False) -> BasicViewPerson:
        person_response = BasicViewPerson(
            id=person_entity.id,
            first_name=person_entity.first_name,
            last_name=person_entity.last_name,
            email=person_entity.email,
            mobile_number=person_entity.mobile_number,
            date_of_birth=person_entity.date_of_birth,
            gender=person_entity.gender,
        )
        if include_profile_image and person_entity.profile_images:
            images = sorted(person_entity.profile_images, key=lambda x: x.id, reverse=True)
            if len(images) > 0 and images[0] is not None:
                person_response.profile_image = self.media_factory.create_view_media_item_from_media_item_entity(images[0].image)

        return person_response

    def create_person_from_person_entity(self, person_entity: models.Person, include_households=True, include_profile_image=False, user: DisplayUser = None) -> FullViewPerson:
        profile = {name: getattr(person_entity, name, None) for name in PROFILE_PERSON_FIELDS}
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
            archived_at=getattr(person_entity, "archived_at", None),
            **profile,
        )
        if person_entity.social_media_links:
            for sml in person_entity.social_media_links:
                sml_response = SocialMediaLink(type=sml.type, url=sml.url)
                person_response.social_media_links.append(sml_response)

        for email in _loaded(person_entity, "emails"):
            person_response.emails.append(PersonEmailView(id=email.id, email=email.email, is_primary=bool(email.is_primary), label=email.label))
        for phone in _loaded(person_entity, "phones"):
            person_response.phones.append(PersonPhoneView(id=phone.id, number=phone.number, phone_type=phone.phone_type, is_primary=bool(phone.is_primary), label=phone.label))
        for contact in _loaded(person_entity, "emergency_contacts"):
            person_response.emergency_contacts.append(EmergencyContactView(
                id=contact.id,
                name=contact.name,
                relationship_label=contact.relationship_label,
                phone=contact.phone,
                email=contact.email,
                notes=contact.notes,
            ))
        for link in _loaded(person_entity, "category_links"):
            if link.category is not None:
                person_response.categories.append(CategoryView(
                    id=link.category.id,
                    name=link.category.name,
                    description=link.category.description,
                    colour=link.category.colour,
                    active=link.category.active,
                ))
        for link in _loaded(person_entity, "service_type_links"):
            if link.service_type is not None:
                person_response.service_types.append(ServiceTypeView(
                    id=link.service_type.id,
                    name=link.service_type.name,
                    description=link.service_type.description,
                    active=link.service_type.active,
                ))

        if person_entity.addresses:
            for people_address in person_entity.addresses:
                address = people_address.address
                address_response = self.address_factory.create_address_from_address_entity(address)

                person_response.addresses.append(address_response)

        if include_households and person_entity.households:
            person_response.households = []
            for household in person_entity.households:
                household_response = self.create_household_view(household)
                person_response.households.append(household_response)


        if include_profile_image and person_entity.profile_images:
            images = sorted(person_entity.profile_images, key=lambda x: x.id, reverse=True)
            if len(images) > 0 and images[0] is not None:
                person_response.profile_image = self.media_factory.create_view_media_item_from_media_item_entity(images[0].image)


        if user is not None:
            person_response.user = user

        if person_response.user is None and person_entity.user is not None:
            person_response.user = DisplayUser(
                id=person_entity.user.id,
                first_name=person_entity.user.first_name,
                last_name=person_entity.user.last_name,
                email=person_entity.user.email,
                mobile_number=person_entity.user.mobile_number
            )
        person_response.has_account = person_response.user is not None
        return person_response

    def create_household_view(self, household) -> ViewHousehold:
        people = []
        for household_person in household.people:
            person = self.create_basic_person_view_from_person_entity(household_person, include_profile_image=True)
            people.append(person)

        view_household = ViewHousehold(
            id=household.id,
            name=getattr(household, "name", None),
            notes=getattr(household, "notes", None),
            leader=self.create_basic_person_view_from_person_entity(household.leader),
            address=self.address_factory.create_address_from_address_entity(household.address),
            people=people,
        )

        h_images = sorted(household.household_images, key=lambda x: x.id, reverse=True)
        if len(h_images) > 0 and h_images[0] is not None:
            view_household.household_image = self.media_factory.create_view_media_item_from_media_item_entity(
                h_images[0].image)

        return view_household

    def create_profile_image_list_from_entity_list(self, profile_images) -> List[ViewMediaItem]:
        person_images = sorted(profile_images, key=lambda x: x.id, reverse=True)
        profile_image_list: List[ViewMediaItem] = []
        for person_image in person_images:
            profile_image_list.append(self.media_factory.create_media_item_from_media_item_entity(person_image.image))
        return profile_image_list

    def create_person_entity_from_create_person(self, person: CreatePerson, address_entities=None) -> models.Person:
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
        for name in PROFILE_PERSON_FIELDS:
            setattr(new_person, name, getattr(person, name, None))
        self._append_contacts(new_person, person)
        if person.social_media_links:
            for sml in person.social_media_links:
                new_sml = models.SocialMediaLink(type=sml.type, url=sml.url)
                new_person.social_media_links.append(new_sml)

        if address_entities is not None:
            # TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
            # multiple rows in the DB for the same address
            for address_entity in address_entities:
                pa = models.PeopleAddress(address=address_entity, person=new_person)
                new_person.addresses.append(pa)

        return new_person

    def _append_contacts(self, new_person, person: CreatePerson):
        if person.emails:
            for item in person.emails:
                new_person.emails.append(models.PersonEmail(email=str(item.email), is_primary=item.is_primary, label=item.label))
            self._one_primary(new_person.emails)
            new_person.email = str(next(item.email for item in new_person.emails if item.is_primary))
        elif person.email:
            new_person.emails.append(models.PersonEmail(email=str(person.email), is_primary=True))

        if person.phones:
            for item in person.phones:
                new_person.phones.append(models.PersonPhone(
                    number=item.number,
                    phone_type=item.phone_type or "mobile",
                    is_primary=item.is_primary,
                    label=item.label,
                ))
            self._one_primary(new_person.phones)
            primary = next(item for item in new_person.phones if item.is_primary)
            if primary.phone_type == "mobile" or person.mobile_number is None:
                new_person.mobile_number = primary.number
        elif person.mobile_number:
            new_person.phones.append(models.PersonPhone(number=person.mobile_number, phone_type="mobile", is_primary=True))

        for contact in person.emergency_contacts or []:
            new_person.emergency_contacts.append(models.EmergencyContact(
                name=contact.name,
                relationship_label=contact.relationship_label,
                phone=contact.phone,
                email=str(contact.email) if contact.email else None,
                notes=contact.notes,
            ))

    def _one_primary(self, items):
        if not items:
            return
        primaries = [item for item in items if item.is_primary]
        if not primaries:
            items[0].is_primary = True
        else:
            for extra in primaries[1:]:
                extra.is_primary = False
