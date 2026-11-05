from unittest import mock

import pytest

from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.models.database import models
from src.app.people.models.people import AddressType, CreateAddress, UpdateAddress, ViewAddress
from src.app.people.services.addressService import AddressAlreadyExists, AddressService, NoAddressException


def _build_service():
    return AddressService(addressDAO=AddressDAO(), addressFactory=AddressFactory())


@mock.patch.object(AddressFactory, "create_address_from_address_entity")
@mock.patch.object(AddressDAO, "get_all_addresses")
def test_get_all_addresses(mock_get_all, mock_create_address):
    service = _build_service()
    entity = models.Address(id=1, type="home", city="Cape Town")
    mock_get_all.return_value = [entity]
    view = ViewAddress(id=1, type="home", city="Cape Town")
    mock_create_address.return_value = view

    result = list(service.get_all_addresses())

    assert result == [view]


@mock.patch.object(AddressFactory, "create_address_from_address_entity")
@mock.patch.object(AddressDAO, "get_address_by_id")
def test_get_by_id(mock_get_by_id, mock_create_address):
    service = _build_service()
    entity = models.Address(id=1, type="home")
    mock_get_by_id.return_value = entity
    view = ViewAddress(id=1, type="home")
    mock_create_address.return_value = view

    assert service.get_by_id(1) == view


@mock.patch.object(AddressDAO, "get_address_by_id")
def test_get_by_id_missing(mock_get_by_id):
    service = _build_service()
    mock_get_by_id.return_value = None

    with pytest.raises(NoAddressException):
        service.get_by_id(99)


@mock.patch.object(AddressFactory, "create_address_from_address_entity")
@mock.patch.object(AddressDAO, "find_address")
def test_find_address_found(mock_find, mock_create_address):
    service = _build_service()
    entity = models.Address(id=1, type="home", street="Main")
    mock_find.return_value = entity
    view = ViewAddress(id=1, type="home", street="Main")
    mock_create_address.return_value = view

    result = service.find_address("home", "1", "Main", "Sub", "City", "Prov", "ZA", "0001")

    assert result == view


@mock.patch.object(AddressDAO, "find_address")
def test_find_address_missing(mock_find):
    service = _build_service()
    mock_find.return_value = None

    assert service.find_address("home", "1", "Main", "Sub", "City", "Prov", "ZA", "0001") is None


@mock.patch.object(AddressFactory, "create_address_from_address_entity")
@mock.patch.object(AddressDAO, "get_address_by_id")
@mock.patch.object(AddressDAO, "update_address")
def test_update_address(mock_update, mock_get_by_id, mock_create_address):
    service = _build_service()
    existing = models.Address(id=1, type="home")
    updated_entity = models.Address(id=1, type="business", street="New")
    mock_get_by_id.side_effect = [existing, updated_entity]
    view = ViewAddress(id=1, type="business", street="New")
    mock_create_address.return_value = view
    payload = UpdateAddress(
        id=1,
        type=AddressType.business,
        street_number="2",
        street="New",
        suburb="Sub",
        city="City",
        province="Prov",
        country="ZA",
    )

    result = service.update_address(1, payload)

    assert result == view
    assert payload.id == 1
    mock_update.assert_called_once()


@mock.patch.object(AddressDAO, "get_address_by_id")
def test_update_address_missing(mock_get_by_id):
    service = _build_service()
    mock_get_by_id.return_value = None

    with pytest.raises(NoAddressException):
        service.update_address(
            1,
            UpdateAddress(
                id=1,
                type=AddressType.home,
                street_number="1",
                street="Main",
                suburb="Sub",
                city="City",
                province="Prov",
                country="ZA",
            ),
        )


@mock.patch.object(AddressService, "get_by_id")
@mock.patch.object(AddressDAO, "create_address")
@mock.patch.object(AddressFactory, "create_address_entity_from_address")
@mock.patch.object(AddressDAO, "find_address")
def test_create_address_success(mock_find, mock_create_entity, mock_create_address, mock_get_by_id):
    service = _build_service()
    mock_find.return_value = None
    entity = models.Address(id=1, type="home")
    mock_create_entity.return_value = entity
    mock_create_address.return_value = entity
    view = ViewAddress(id=1, type="home")
    mock_get_by_id.return_value = view
    payload = CreateAddress(
        type=AddressType.home,
        street_number="1",
        street="Main",
        suburb="Sub",
        city="City",
        province="Prov",
        country="ZA",
    )

    result = service.create_address(payload)

    assert result == view


@mock.patch.object(AddressFactory, "create_address_from_address_entity")
@mock.patch.object(AddressDAO, "find_address")
def test_create_address_already_exists(mock_find, mock_create_address):
    service = _build_service()
    existing = models.Address(id=5, type="home")
    mock_find.return_value = existing
    view = ViewAddress(id=5, type="home")
    mock_create_address.return_value = view

    with pytest.raises(AddressAlreadyExists) as exc:
        service.create_address(
            CreateAddress(
                type=AddressType.home,
                street_number="1",
                street="Main",
                suburb="Sub",
                city="City",
                province="Prov",
                country="ZA",
            )
        )

    assert exc.value.existing_address.id == 5
