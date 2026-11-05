from datetime import datetime
from unittest import mock

from src.app.church.factories.churchFactory import ChurchFactory
from src.app.church.models.church import CreateChurch
from src.app.church.models.database import models
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models as media_models
from src.app.media.models.media import ViewMediaItem
from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.models.database import models as people_models
from src.app.people.models.people import ViewAddress


def test_create_church_entity_from_church():
    factory = ChurchFactory(address_factory=AddressFactory(), media_factory=MediaFactory())
    church = CreateChurch(
        name="Flocki",
        description="Community church",
        email="info@flocki.org",
        phone="+27000",
        website="https://flocki.org",
        address_id=2,
        logo_image_id=3,
    )

    entity = factory.create_church_entity_from_church(church)

    assert entity.name == "Flocki"
    assert entity.address_id == 2
    assert entity.logo_image_id == 3
    assert entity.website == "https://flocki.org"


def test_create_church_from_church_entity_none():
    factory = ChurchFactory(address_factory=AddressFactory(), media_factory=MediaFactory())
    assert factory.create_church_from_church_entity(None) is None


@mock.patch.object(MediaFactory, "create_view_media_item_from_media_item_entity")
@mock.patch.object(AddressFactory, "create_address_from_address_entity")
def test_create_church_from_church_entity_with_relations(mock_create_address, mock_create_logo):
    address_factory = AddressFactory()
    media_factory = MediaFactory()
    factory = ChurchFactory(address_factory=address_factory, media_factory=media_factory)

    entity = models.Church(
        id=1,
        name="Flocki",
        description="desc",
        email="info@flocki.org",
        phone="+27000",
        website="https://flocki.org",
        created=datetime(2024, 1, 1),
    )
    entity.address = people_models.Address(id=2, type="church", street="Main", city="Cape Town")
    entity.logo_image = media_models.MediaItem(id=3, store="local", address="a", created=datetime.now())
    mock_create_address.return_value = ViewAddress(id=2, type="church", street="Main", city="Cape Town")
    mock_create_logo.return_value = ViewMediaItem(id=3, description="logo")

    view = factory.create_church_from_church_entity(entity)

    assert view.id == 1
    assert view.name == "Flocki"
    assert view.address.id == 2
    assert view.logo_image.id == 3
