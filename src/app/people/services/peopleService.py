from datetime import datetime

from fastapi import Depends, UploadFile
from fastapi.responses import FileResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.services.mediaService import MediaService, NoImageException
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import CreatePerson, UpdatePerson

import uuid
from mimetypes import guess_extension

from src.app.people.daos.householdDAO import HouseholdDAO
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.householdUtils import HouseholdUtils
from src.app.utils.DateUtils import DateUtils


class NoPersonException(Exception):
    pass


class NoHouseholdExceptionForPersonCreation(Exception):
    pass


class UnableToRemoveLeaderFromHouseholdException(Exception):
    pass


class PeopleService:
    def __init__(self, peopleDAO: PeopleDAO = Depends(PeopleDAO), addressDAO: AddressDAO = Depends(AddressDAO),
                 media_DAO: MediaDAO = Depends(MediaDAO),
                 media_service: MediaService = Depends(MediaService),
                 people_factory: PeopleFactory = Depends(PeopleFactory),
                 media_factory: MediaFactory = Depends(MediaFactory),
                 household_DAO: HouseholdDAO = Depends(HouseholdDAO),
                 household_utils: HouseholdUtils = Depends(HouseholdUtils)):
        self.peopleDAO = peopleDAO
        self.peopleFactory = people_factory
        self.addressDAO = addressDAO
        self.media_factory = media_factory
        self.media_DAO = media_DAO
        self.media_service = media_service
        self.household_DAO = household_DAO
        self.household_utils = household_utils

    def get_all(self):
        people_response = []
        people = self.peopleDAO.get_all()
        for person in people:
            people_response.append(
                self.peopleFactory.create_person_from_person_entity(person_entity=person, include_profile_image=True,
                                                                    include_households=True))
        return people_response

    def get_by_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            return None
        return self.peopleFactory.create_person_from_person_entity(person_entity)

    # TODO refactor this code a bit so that the local vs s3 logic can be centralized
    def get_profile_image_by_person_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            raise NoPersonException("No person with that Id")
        person_with_profile_image = self.peopleFactory.create_person_from_person_entity(person_entity, False, True)
        if person_with_profile_image is None:
            return None
        else:
            full_profile_image_info = self.media_DAO.get_image_by_id(person_with_profile_image.profile_image.id)

            if full_profile_image_info is None:
                return None
            elif full_profile_image_info.store is not None and full_profile_image_info.store == 'local':
                return FileResponse(full_profile_image_info.address)
            elif full_profile_image_info.store is not None and full_profile_image_info.store == 's3':
                raise NotImplementedError("S3 not implemented")

            return None

    # TODO fis this code for new address int array on person
    def update_person(self, id: int, person: UpdatePerson):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            raise NoPersonException(
                "No person with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        # For update requests the model is not expected to come in with an ID since it is passed in the URL.
        person.id = person_entity.id
        update_values = person.dict()

        # validate that households are correct.
        household_ids = update_values.pop('household_ids', person.dict())
        self.validate_households(household_ids)
        # validate potential removal of persons
        self.validate_household_remove_person(household_ids, person_entity)
        # validate address ids
        self.validate_addresses(person.addresses)
        # validate image id
        self.validate_image_id(person.profile_image_id)

        # start updating record
        smls = update_values.pop('social_media_links', person.dict())
        if smls is not None:
            existing_social_media_links = self.peopleDAO.get_existing_social_media_links(person.id)
            if existing_social_media_links:
                for existing_sml in existing_social_media_links:
                    self.peopleDAO.delete_social_media_link(existing_sml.id)

            for sml in smls:
                self.peopleDAO.create_social_media_link(person.id, sml['type'], sml['url'])

        addresses = update_values.pop('addresses', person.dict())
        if addresses is not None:
            existing_people_addresses = self.addressDAO.get_existing_addresses_for_person(person.id)
            if existing_people_addresses is not None:
                for existing_people_address in existing_people_addresses:
                    self.addressDAO.delete_address(existing_people_address.id)

            # TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
            # multiple rows in the DB for the same address
            for address_id in addresses:
                address = self.addressDAO.get_address_by_id(address_id)
                self.addressDAO.create_address_linked_to_person(address, person_entity)

        image_entity = None
        profile_image_id = update_values.pop('profile_image_id', person.dict())
        if profile_image_id is not None:
            image_entity = self.media_DAO.get_image_by_id(profile_image_id)


        self.peopleDAO.update_person(person_entity.id, update_values, image_entity)
        if household_ids is not None:
            self.update_households_for_person(household_ids, person_entity)

        return self.peopleFactory.create_person_from_person_entity(self.peopleDAO.get_person_by_id(id), include_households=True, include_profile_image=True)

    def validate_image_id(self, profile_image_id):
        if profile_image_id is not None:
            image_entity = self.media_DAO.get_image_by_id(profile_image_id)
            if image_entity is None:
                raise NoImageException(f"Image with id: {profile_image_id} does not exist")

    def validate_addresses(self, addresses):
        for address_id in addresses:
            address = self.addressDAO.get_address_by_id(address_id)
            if address is None:
                raise NoAddressException(f"Address with id: {address_id} does not exist")

    def update_households_for_person(self, new_household_ids, personToUpdate):
        existing_household_ids = self.household_utils.get_existing_household_ids(personToUpdate)
        household_ids_to_add = self.household_utils.get_household_ids_to_add(existing_household_ids, new_household_ids)
        household_ids_to_remove = self.household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids)

        if household_ids_to_add:
            for household_id in household_ids_to_add:
                self.household_DAO.add_person_to_household(self.household_DAO.get_household_by_id(household_id), personToUpdate)
        if household_ids_to_remove:
            for household_id in household_ids_to_remove:
                self.household_DAO.remove_person_from_household(self.household_DAO.get_household_by_id(household_id), personToUpdate)


    def create_person(self, person: CreatePerson):
        self.validate_households(person.household_ids)
        # validate address ids
        self.validate_addresses(person.addresses)
        # validate image id
        self.validate_image_id(person.profile_image_id)

        image_entity = None
        if person.profile_image_id is not None:
            image_entity = self.media_DAO.get_image_by_id(person.profile_image_id)
        address_entities = []
        for address_id in person.addresses:
            address_entities.append(self.addressDAO.get_address_by_id(address_id))
        new_person = self.peopleFactory.create_person_entity_from_create_person(person, address_entities)

        if new_person.registered_date is None:
            new_person.registered_date = DateUtils.get_current_datetime()

        created_person = self.peopleDAO.create_person(new_person, image_entity)
        if person.household_ids is not None:
            self.add_person_to_households(created_person, person.household_ids)
        return self.peopleFactory.create_person_from_person_entity(self.peopleDAO.get_person_by_id(created_person.id), include_households=True, include_profile_image=True)

    def validate_household_remove_person(self, new_household_ids, personToUpdate):
        existing_household_ids = self.household_utils.get_existing_household_ids(personToUpdate)
        household_ids_to_remove = self.household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids)
        for(household_id) in household_ids_to_remove:
            household_entity = self.household_DAO.get_household_by_id(household_id)
            if household_entity.leader.id == personToUpdate.id:
                raise UnableToRemoveLeaderFromHouseholdException(
                f"You cannot remove a leader [id='{personToUpdate.id}'] from a household [id='{household_entity.id}']. You must first assign a new leader to the household.")

    def validate_households(self, household_ids):
        if household_ids is not None:
            for household_id in household_ids:
                household_entity = self.household_DAO.get_household_by_id(household_id)
                if household_entity is None:
                    # TODO if this happens at this stage the person would have already have been created.
                    raise NoHouseholdExceptionForPersonCreation(f"No household with that Id: {household_id}")


    def upload_profile_image(self, id, file: UploadFile):
        personToUpdate = self.peopleDAO.get_person_by_id(id)
        if personToUpdate is None:
            raise NoPersonException(
                "No person with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        if file is not None:
            if file.content_type == 'image/jpeg':
                file.content_type = 'image/jpg'  # TODO this is a bit of hack to make sure the extension is .jpg and not .jpe
            filename = str(personToUpdate.id) + '_' + str(uuid.uuid4()) + guess_extension(
                file.content_type, strict=False).strip()
            description = f"Profile image for user: {personToUpdate.first_name}  {personToUpdate.last_name}  with ID: {personToUpdate.id}"
            image_entity = self.media_service.upload_image(file, filename, description)
            self.peopleDAO.add_person_image(personToUpdate, image_entity)
            return self.media_factory.create_image_from_image_entity(image_entity)

    def get_profile_images_by_person_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            raise NoPersonException("No person with that Id")
        return self.peopleFactory.create_profile_image_list_from_entity_list(person_entity)

    # I would have prefered adding this method to the household service, and make each service only dependent on it's own DAO,
    # but I couldn't get it to work due to circular dependencies.
    def add_person_to_households(self, person, household_entity_ids):
        # household_entity_ids should have been validated by now.
        for household_id in household_entity_ids:
            household_entity = self.household_DAO.get_household_by_id(household_id)
            self.household_DAO.add_person_to_household(household_entity, person)

    def remove_person_from_households(self, person, household_entity_ids):
        # household_entity_ids should have been validated by now.
        for household_id in household_entity_ids:
            household_entity = self.household_DAO.get_household_by_id(household_id)
            self.household_DAO.remove_person_from_household(household_entity, person)

