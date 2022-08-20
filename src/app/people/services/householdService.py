import uuid
from mimetypes import guess_extension

from fastapi import Depends
from starlette.responses import FileResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.services.mediaService import MediaService
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.daos.householdDAO import HouseholdDAO

from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.household import CreateHousehold


class NoHouseholdException(Exception):
    pass

class LeaderMustBeMemberOfHouseholdException(Exception):
    pass

class HouseholdService:
    def __init__(self, household_DAO: HouseholdDAO = Depends(HouseholdDAO), household_factory: HouseholdFactory = Depends(HouseholdFactory),
                 peopleDAO: PeopleDAO = Depends(PeopleDAO), people_factory: PeopleFactory = Depends(PeopleFactory),
                 media_service: MediaService = Depends(MediaService), media_DAO: MediaDAO = Depends(MediaDAO),
                 media_factory: MediaFactory = Depends(MediaFactory)):
        self.people_DAO = peopleDAO
        self.people_factory = people_factory
        self.household_factory = household_factory
        self.household_DAO = household_DAO
        self.media_service = media_service
        self.media_DAO = media_DAO
        self.media_factory = media_factory

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
        for person_id in household.people:
            person_entity = self.people_DAO.get_person_by_id(person_id)
            if not person_entity:
                raise Exception(f"Person does not exist with ID: {person_id}")
            people_models.append(person_entity)

        image_entity = self.media_DAO.get_image_by_id(household.household_image)
        new_household = self.household_factory.createHouseholdEntityFromHousehold(household, people_models)
        return self.household_factory.createHouseholdFromHouseholdEntity(self.household_DAO.add_household(new_household, image_entity), True)


    def get_household_images_by_household_id(self, id):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException("No household with that Id")
        return self.household_factory.create_household_image_list_from_entity_list(household_entity)

    def upload_household_image(self, id, file):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(
                "No household with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

        if file is not None:
            if file.content_type == 'image/jpeg':
                file.content_type = 'image/jpg'  # TODO this is a bit of hack to make sure the extension is .jpg and not .jpe

            filename = 'household_' + str(household_entity.id) + '_' + str(uuid.uuid4()) + guess_extension(
                file.content_type, strict=False).strip()
            description = f"Profile image for household with ID: {household_entity.id}"
            image_entity = self.media_service.upload_image(file, filename, description)
            self.household_DAO.add_household_image(household_entity, image_entity)
            return self.media_factory.createImageFromImageEntity(image_entity)

    def get_household_image_by_household_id(self, id):
        household_entity = self.household_DAO.get_household_by_id(id)
        if household_entity is None:
            raise NoHouseholdException(
                "No household with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        household_with_image = self.household_factory.createHouseholdFromHouseholdEntity(household_entity, True)
        if household_with_image is None:
            return None
        elif household_with_image.household_image is None:
            return None
        elif household_with_image.household_image.store is not None and household_with_image.household_image.store == 'local':
            return FileResponse(household_with_image.household_image.address)
        elif household_with_image.household_image.store is not None and household_with_image.household_image.store == 's3':
            return NotImplementedError("S3 not implemented")
        return

