from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.models.database import models
from src.app.people.models.people import AddressType, CreateAddress


def test_create_address_entity_from_address():
    factory = AddressFactory()
    address = CreateAddress(
        type=AddressType.home,
        street_number="21",
        street="Allan",
        suburb="Noordwyk",
        city="Midrand",
        province="GP",
        country="ZA",
        postal_code="1685",
        latitude=-26.0,
        longitude=28.0,
    )

    entity = factory.create_address_entity_from_address(address)

    assert entity.type == AddressType.home
    assert entity.street == "Allan"
    assert entity.latitude == -26.0


def test_create_address_from_address_entity():
    factory = AddressFactory()
    entity = models.Address(
        id=7,
        type="business",
        street_number="10",
        street="Main",
        suburb="CBD",
        city="Cape Town",
        province="WC",
        country="ZA",
        postal_code="8001",
    )

    view = factory.create_address_from_address_entity(entity)

    assert view.id == 7
    assert view.type == "business"
    assert view.city == "Cape Town"
