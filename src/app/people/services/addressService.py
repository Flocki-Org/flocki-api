from fastapi import Depends

from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.models.people import UpdateAddress, CreateAddress, ViewAddress


class NoAddressException(Exception):
    pass

class AddressAlreadyExists(Exception):
    def __init__(self, existing_address: ViewAddress):
        self.existing_address = existing_address

class AddressService:
    def __init__(self, addressDAO: AddressDAO = Depends(AddressDAO), addressFactory: AddressFactory = Depends(AddressFactory)):
        self.addressDAO = addressDAO
        self.addressFactory = addressFactory

    def get_all_addresses(self):
        addresses = self.addressDAO.get_all_addresses()
        for address in addresses:
            yield self.addressFactory.create_address_from_address_entity(address)

    def get_by_id(self, id):
        address_entity = self.addressDAO.get_address_by_id(id)
        if address_entity is None:
            raise NoAddressException("No address with that Id")
        return self.addressFactory.create_address_from_address_entity(address_entity)

    def find_address(self, type: str, street_number:str, street: str, suburb:str, city: str, province: str, country:str, postal_code: str):
        address_entity = self.addressDAO.find_address(type, street_number, street, suburb, city, province, country, postal_code)
        if address_entity is None:
            return None
        return self.addressFactory.create_address_from_address_entity(address_entity)

    def update_address(self, id: int, address: UpdateAddress):
        address_entity = self.addressDAO.get_address_by_id(id)
        if address_entity is None:
            raise NoAddressException("No address with that Id")  # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

        # For update requests the model is not expected to come in with an ID since it is passed in the URL.
        address.id = address_entity.id

        update_values = address.dict()

        self.addressDAO.update_address(address.id, update_values)
        return self.addressFactory.create_address_from_address_entity(self.addressDAO.get_address_by_id(id))

    def create_address(self, address: CreateAddress):
        existing_address = self.addressDAO.find_address(address.type, address.street_number, address.street, address.suburb, address.city, address.province, address.country, address.postal_code)
        if(existing_address is not None):
            raise AddressAlreadyExists(self.addressFactory.create_address_from_address_entity(existing_address))

        new_address = self.addressFactory.create_address_entity_from_address(address)

        created_address = self.addressDAO.create_address(new_address)
        return self.get_by_id(created_address.id)
