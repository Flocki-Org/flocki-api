from fastapi import Depends, UploadFile
from fastapi.responses import FileResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.services.mediaService import MediaService
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import Person, UpdatePerson
import uuid
from mimetypes import guess_extension


class NoPersonException(Exception):
    pass


class PeopleService:
    def __init__(self, peopleDAO: PeopleDAO = Depends(PeopleDAO), addressDAO: AddressDAO = Depends(AddressDAO),
                 media_DAO: MediaDAO = Depends(MediaDAO),
                 media_service: MediaService = Depends(MediaService),
                 people_factory: PeopleFactory = Depends(PeopleFactory),
                 media_factory: MediaFactory = Depends(MediaFactory)):
        self.peopleDAO = peopleDAO
        self.peopleFactory = people_factory
        self.addressDAO = addressDAO
        self.media_factory = media_factory
        self.media_DAO = media_DAO
        self.media_service = media_service

    def get_all(self):
        people_response = []
        people = self.peopleDAO.get_all()
        for person in people:
            people_response.append(self.peopleFactory.createPersonFromPersonEntity(person_entity=person, include_profile_image=True, include_household=True))
        return people_response

    def get_by_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            return None
        return self.peopleFactory.createPersonFromPersonEntity(person_entity)

    #TODO refactor this code a bit so that the local vs s3 logic can be centralized
    def get_profile_image_by_person_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            raise NoPersonException("No person with that Id")
        person_with_profile_image = self.peopleFactory.createPersonFromPersonEntity(person_entity, False, True)
        if person_with_profile_image is None:
            return None
        elif person_with_profile_image.profile_image is None:
            return None
        elif person_with_profile_image.profile_image.store is not None and person_with_profile_image.profile_image.store == 'local':
            return FileResponse(person_with_profile_image.profile_image.address)
        elif person_with_profile_image.profile_image.store is not None and person_with_profile_image.profile_image.store == 's3':
            return NotImplementedError("S3 not implemented")
        return

    def update_person(self, id: int, person: UpdatePerson):
        personToUpdate = self.peopleDAO.get_person_by_id(id)
        if personToUpdate is None:
            raise NoPersonException(
                "No person with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        # For update requests the model is not expected to come in with an ID since it is passed in the URL.
        person.id = personToUpdate.id

        update_values = person.dict()
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
            for address in addresses:
                self.addressDAO.create_address(address, personToUpdate)

        profile_image_id = update_values.pop('profile_image_id', person.dict())
        if profile_image_id is not None:
            image_entity = self.media_DAO.get_image_by_id(profile_image_id)

        self.peopleDAO.update_person(personToUpdate.id, update_values, image_entity)
        return self.peopleFactory.createPersonFromPersonEntity(self.peopleDAO.get_person_by_id(id), True, True)

    def create_person(self, person):
        new_person = self.peopleFactory.createPersonEntityFromPerson(person)
        created_person = self.peopleDAO.create_person(new_person)
        return self.get_by_id(created_person.id)

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
            updated_person = self.peopleDAO.get_person_by_id(personToUpdate.id)
            return self.peopleFactory.createPersonFromPersonEntity(updated_person, False, True)

    def get_profile_images_by_person_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            raise NoPersonException("No person with that Id")
        return self.peopleFactory.create_profile_image_list_from_entity_list(person_entity)
