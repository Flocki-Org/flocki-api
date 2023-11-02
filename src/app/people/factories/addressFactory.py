from ...people.models.database import models
from ...people.models.people import CreateAddress, ViewAddress


class AddressFactory:
    #create and Address Entity From and Address Model
    def create_address_entity_from_address(self, address):
        address_entity = models.Address(
            type=address.type,
            street_number=address.street_number,
            street=address.street,
            suburb=address.suburb,
            city=address.city,
            province=address.province,
            country=address.country,
            postal_code=address.postal_code,
            latitude=address.latitude,
            longitude=address.longitude)

        return address_entity

    def create_address_from_address_entity(self, address_entity):
        return ViewAddress(
            id=address_entity.id,
            type=address_entity.type,
            street_number=address_entity.street_number,
            street=address_entity.street,
            suburb=address_entity.suburb,
            city=address_entity.city,
            province=address_entity.province,
            country=address_entity.country,
            postal_code=address_entity.postal_code,
            latitude=address_entity.latitude,
            longitude=address_entity.longitude)