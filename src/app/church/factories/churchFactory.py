from fastapi import Depends

from ...church.models.database import models
from ...church.models.church import CreateChurch, ViewChurch
from ...media.factories.mediaFactory import MediaFactory
from ...people.factories.addressFactory import AddressFactory


class ChurchFactory:

    def __init__(self,  address_factory: AddressFactory = Depends(AddressFactory), media_factory: MediaFactory = Depends(MediaFactory)):
        self.address_factory = address_factory
        self.media_factory = media_factory

    def create_church_entity_from_church(self, church):
        church_entity = models.Church(
                name=church.name,
                description=church.description,
                address_id=church.address_id,
                phone=church.phone,
                email=church.email,
                website=church.website,
                logo_image_id=church.logo_image_id)
        return church_entity

    def create_church_from_church_entity(self, church_entity) -> ViewChurch:
        if church_entity is None:
            return None

        address_response = None
        if church_entity.address is not None:
            address_response = self.address_factory.create_address_from_address_entity(church_entity.address)

        logo_image_response = None
        if church_entity.logo_image is not None:
            logo_image_response = self.media_factory.create_view_image_from_image_entity(church_entity.logo_image)

        return ViewChurch(
            id=church_entity.id,
            created=church_entity.created,
            name=church_entity.name,
            description=church_entity.description,
            address=address_response,
            logo_image=logo_image_response,
            phone=church_entity.phone,
            email=church_entity.email,
            website=church_entity.website)
