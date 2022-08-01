from fastapi import Depends

from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import Person


class NoPersonException(Exception):
    pass

class PeopleService:
    def __init__(self, peopleDAO: PeopleDAO = Depends(PeopleDAO), adressDAO: AddressDAO = Depends(AddressDAO), peopleFactory: PeopleFactory = Depends(PeopleFactory)):
        self.peopleDAO = peopleDAO
        self.peopleFactory = peopleFactory
        self.adressDAO = adressDAO

    def get_all(self):
        people_response = []
        people = self.peopleDAO.get_all()
        for person in people:
            people_response.append(self.peopleFactory.createPersonFromPersonEntity(person_entity=person))
        return people_response

    def get_by_id(self, id):
        person_entity = self.peopleDAO.get_person_by_id(id)
        if person_entity is None:
            return None
        return self.peopleFactory.createPersonFromPersonEntity(person_entity)

    def update_person(self, id:int, person: Person):
        personToUpdate = self.peopleDAO.get_person_by_id(id)
        if personToUpdate is None:
            raise NoPersonException("No person with that Id") #HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
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
            existing_people_addresses = self.adressDAO.get_existing_addresses_for_person(person.id)
            if existing_people_addresses is not None:
                for existing_people_address in existing_people_addresses:
                    self.adressDAO.delete_address(existing_people_address.id)

            # TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
            # multiple rows in the DB for the same address
            for address in addresses:
                self.adressDAO.create_address(address, personToUpdate)

        update_values.pop('household', person.dict())

        self.peopleDAO.update_person(personToUpdate.id, update_values)
        #self.db.commit()
        return self.get_by_id(person.id)

    def create_person(self, person):
        new_person = self.peopleFactory.createPersonEntityFromPerson(person)
        created_person = self.peopleDAO.create_person(new_person)
        return self.get_by_id(created_person.id)
