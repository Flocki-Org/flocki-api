import uuid
from mimetypes import guess_extension
from typing import List

from fastapi import Depends, UploadFile
from starlette.responses import FileResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.services.mediaService import MediaService, NoImageException
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.daos.householdDAO import HouseholdDAO

from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.household import CreateHousehold, UpdateHousehold, ViewHousehold
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.householdUtils import HouseholdUtils
from src.app.people.services.peopleService import NoPersonException


class NoHouseholdException(Exception):
    pass


class LeaderMustBeMemberOfHouseholdException(Exception):
    pass


class HouseholdService:
    def __init__(self, household_DAO: HouseholdDAO = Depends(HouseholdDAO), household_factory: HouseholdFactory = Depends(HouseholdFactory),
                 peopleDAO: PeopleDAO = Depends(PeopleDAO), people_factory: PeopleFactory = Depends(PeopleFactory),
                 media_service: MediaService = Depends(MediaService), media_DAO: MediaDAO = Depends(MediaDAO),
                 media_factory: MediaFactory = Depends(MediaFactory), address_DAO: AddressDAO = Depends(AddressDAO),
                 household_utils: HouseholdUtils = Depends(HouseholdUtils)):
        self.people_DAO = peopleDAO
        self.people_factory = people_factory
        self.household_factory = household_factory
        self.household_DAO = household_DAO
        self.media_service = media_service
        self.media_DAO = media_DAO
        self.media_factory = media_factory
        self.address_DAO = address_DAO
        self.household_utils = household_utils

    def get_all_households(self) -> List[ViewHousehold]:
        households_response = []
        households = self.household_DAO.get_all_households()
        for household in households:
            households_response.append(self.household_factory.createHouseholdFromHouseholdEntity(household_entity=household))
        return households_response

    def get_household_by_id(self, id: int):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(f"Household does not exist with the following ID: {id}")
        return self.household_factory.createHouseholdFromHouseholdEntity(household_entity, include_household_image=True)

    def add_household(self, household: CreateHousehold):

        people_entities = []
        invalid_people_ids = []
        for person_id in household.people_ids:
            person_entity = self.people_DAO.get_person_by_id(person_id)
            if not person_entity:
                invalid_people_ids.append(person_id)
            people_entities.append(person_entity)

        if invalid_people_ids is not None and len(invalid_people_ids) > 0:
            raise NoPersonException(f"No people with the following IDs: {invalid_people_ids}")

        leader_entity = self.people_DAO.get_person_by_id(household.leader_id)
        # leader entity can never be None because leader id is required to be in the list of people ids, and so would have
        # failed validation in the previous check above.


        image_entity = self.media_DAO.get_image_by_id(household.household_image_id)
        if image_entity is None:
            raise NoImageException(f"No image with the following ID: {household.household_image_id}")

        new_household = self.household_factory.createHouseholdEntityFromHousehold(household, people_entities)
        return self.household_factory.createHouseholdFromHouseholdEntity(self.household_DAO.add_household(new_household, image_entity), True)

    def get_household_images_by_household_id(self, id):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(f"No household with the following ID: {id}")

        return self.household_factory.create_household_image_list_from_entity_list(household_entity)

    def upload_household_image(self, id, file: UploadFile):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(f"No household with the following ID: {id}")

        if file is not None:
            if file.content_type == 'image/jpeg':
                file.content_type = 'image/jpg'  # TODO this is a bit of hack to make sure the extension is .jpg and not .jpe

            filename = 'household_' + str(household_entity.id) + '_' + str(uuid.uuid4()) + guess_extension(
                file.content_type, strict=False).strip()
            description = f"Profile image for household with ID: {household_entity.id}"
            image_entity = self.media_service.upload_image(file, filename, description)
            self.household_DAO.add_household_image(household_entity, image_entity)
            return self.media_factory.create_image_from_image_entity(image_entity)

    def get_household_image_by_household_id(self, id) -> FileResponse:
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(
                f"No household with the following ID: {id}")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        household_with_image = self.household_factory.createHouseholdFromHouseholdEntity(household_entity, True)
        if household_with_image is None:
            return None
        elif household_with_image.household_image is None:
            return None
        elif household_with_image.household_image.store is not None and household_with_image.household_image.store == 'local':
            return FileResponse(household_with_image.household_image.address)
        elif household_with_image.household_image.store is not None and household_with_image.household_image.store == 's3':
            raise NotImplementedError("S3 not implemented")
        return

    def update_household(self, id, household: UpdateHousehold):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(
                f"No household with the following ID: {id}")

        address_entity = self.address_DAO.get_address_by_id(household.address_id)
        if address_entity is None:
            raise NoAddressException(f"No address with the following ID: {household.address_id}")

        update_values = household.dict()
        update_people_ids = update_values.pop('people_ids', household.dict())
        people_entities = []
        for person_id in update_people_ids:
            person_entity = self.people_DAO.get_person_by_id(person_id)
            if not person_entity:
                raise NoPersonException(f"No person with the following ID: {person_id}")
            people_entities.append(person_entity)

        leader_entity = self.people_DAO.get_person_by_id(household.leader_id)

        image_entity = None
        if household.household_image_id is not None:
            image_entity = self.media_DAO.get_image_by_id(household.household_image_id)
            if not image_entity:
                raise NoImageException(f"No image with the following ID: {household.household_image_id}")

        self.household_DAO.update_household(household_entity, household.leader_id, household.address_id, image_entity)

        existing_people_ids = self.household_utils.get_existing_people_ids(household_entity)
        people_ids_to_add = self.household_utils.get_people_ids_to_add(existing_people_ids, update_people_ids)
        people_ids_to_remove = self.household_utils.get_people_ids_to_remove(existing_people_ids, update_people_ids)

        if people_ids_to_add is not None and len(people_ids_to_add) > 0:
            for person_id in people_ids_to_add:
                self.household_DAO.add_person_to_household(household_entity, self.people_DAO.get_person_by_id(person_id))

        if people_ids_to_remove is not None and len(people_ids_to_remove) > 0:
            for person_id in people_ids_to_remove:
                self.household_DAO.remove_person_from_household(household_entity, self.people_DAO.get_person_by_id(person_id))

        return self.get_household_by_id(id)
