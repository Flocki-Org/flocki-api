from ...people.models.database import models
from ...people.models.people import Address

class AddressFactory:
    #create and Address Entity From and Address Model
    def createAddressEntityFromAddress(self, address):
        address_entity = models.Address(
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

        return address_entity

    def createAddressFromAddressEntity(self, address_entity):
        return Address(
            id=address_entity.id,
            type=address_entity.type,
            streetNumber=address_entity.streetNumber,
            street=address_entity.street,
            suburb=address_entity.suburb,
            city=address_entity.city,
            province=address_entity.province,
            country=address_entity.country,
            postalCode=address_entity.postalCode,
            latitude=address_entity.latitude,
            longitude=address_entity.longitude)