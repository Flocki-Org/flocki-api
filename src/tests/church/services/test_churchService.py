from datetime import datetime
from unittest import mock

import pytest

from src.app.church.daos.churchDAO import ChurchDAO
from src.app.church.factories.churchFactory import ChurchFactory
from src.app.church.models.church import CreateChurch, UpdateChurch, ViewChurch
from src.app.church.models.database import models
from src.app.church.services.churchService import (
    AddressDoesNotExist,
    ChurchAlreadyExists,
    ChurchService,
    LogoImageDoesNotExist,
    NoChurchExists,
)
from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.models.database import models as media_models
from src.app.media.services.mediaService import MediaService
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.models.database import models as people_models


def _build_service():
    return ChurchService(
        church_dao=ChurchDAO(),
        church_factory=ChurchFactory(),
        media_DAO=MediaDAO(),
        address_DAO=AddressDAO(),
        media_service=MediaService(),
    )


@mock.patch.object(ChurchFactory, "create_church_from_church_entity")
@mock.patch.object(ChurchDAO, "get_church")
def test_get_church(mock_get_church, mock_create_church):
    service = _build_service()
    entity = models.Church(id=1, name="Flocki Church", created=datetime.now())
    mock_get_church.return_value = entity
    expected = ViewChurch(id=1, name="Flocki Church")
    mock_create_church.return_value = expected

    assert service.get_church() == expected
    mock_create_church.assert_called_once_with(entity)


@mock.patch.object(ChurchFactory, "create_church_from_church_entity")
@mock.patch.object(ChurchDAO, "create_church")
@mock.patch.object(ChurchFactory, "create_church_entity_from_church")
@mock.patch.object(ChurchDAO, "get_church")
def test_create_church_success(mock_get_church, mock_create_entity, mock_create_church, mock_create_view):
    service = _build_service()
    mock_get_church.return_value = None
    create = CreateChurch(name="New Church", email="info@church.org")
    entity = models.Church(id=1, name="New Church", created=datetime.now())
    mock_create_entity.return_value = entity
    mock_create_church.return_value = entity
    expected = ViewChurch(id=1, name="New Church")
    mock_create_view.return_value = expected

    result = service.create_church(create)

    assert result == expected
    assert entity.created is not None
    mock_create_church.assert_called_once_with(entity)


@mock.patch.object(ChurchDAO, "get_church")
def test_create_church_already_exists(mock_get_church):
    service = _build_service()
    mock_get_church.return_value = models.Church(id=1, name="Existing", created=datetime.now())

    with pytest.raises(ChurchAlreadyExists):
        service.create_church(CreateChurch(name="Another"))


@mock.patch.object(ChurchFactory, "create_church_from_church_entity")
@mock.patch.object(ChurchDAO, "update_church")
@mock.patch.object(AddressDAO, "get_address_by_id")
@mock.patch.object(MediaDAO, "get_media_item_by_id")
def test_update_church_validates_logo_and_address(
    mock_get_media, mock_get_address, mock_update_church, mock_create_view
):
    service = _build_service()
    mock_get_media.return_value = media_models.MediaItem(id=3, store="local", address="a", created=datetime.now())
    mock_get_address.return_value = people_models.Address(id=2)
    entity = models.Church(id=1, name="Updated", created=datetime.now())
    mock_update_church.return_value = entity
    expected = ViewChurch(id=1, name="Updated")
    mock_create_view.return_value = expected

    result = service.update_church(UpdateChurch(id=1, name="Updated", logo_image_id=3, address_id=2))

    assert result == expected
    update_values = mock_update_church.call_args[0][0]
    assert "id" not in update_values
    assert update_values["logo_image_id"] == 3
    assert update_values["address_id"] == 2


@mock.patch.object(MediaDAO, "get_media_item_by_id")
def test_update_church_invalid_logo(mock_get_media):
    service = _build_service()
    mock_get_media.return_value = None

    with pytest.raises(LogoImageDoesNotExist):
        service.update_church(UpdateChurch(name="X", logo_image_id=99))


@mock.patch.object(AddressDAO, "get_address_by_id")
@mock.patch.object(MediaDAO, "get_media_item_by_id")
def test_update_church_invalid_address(mock_get_media, mock_get_address):
    service = _build_service()
    mock_get_media.return_value = media_models.MediaItem(id=1, store="local", address="a", created=datetime.now())
    mock_get_address.return_value = None

    with pytest.raises(AddressDoesNotExist):
        service.update_church(UpdateChurch(name="X", logo_image_id=1, address_id=99))


@mock.patch.object(ChurchFactory, "create_church_from_church_entity")
@mock.patch.object(ChurchDAO, "update_church")
def test_update_church_drops_null_optional_ids(mock_update_church, mock_create_view):
    service = _build_service()
    mock_update_church.return_value = models.Church(id=1, name="X", created=datetime.now())
    mock_create_view.return_value = ViewChurch(id=1, name="X")

    service.update_church(UpdateChurch(name="X", logo_image_id=None, address_id=None))

    update_values = mock_update_church.call_args[0][0]
    assert "logo_image_id" not in update_values
    assert "address_id" not in update_values


@mock.patch.object(ChurchDAO, "delete_church")
@mock.patch.object(ChurchDAO, "get_church")
def test_delete_church_success(mock_get_church, mock_delete_church):
    service = _build_service()
    mock_get_church.return_value = models.Church(id=1, name="X", created=datetime.now())
    mock_delete_church.return_value = None

    service.delete_church()

    mock_delete_church.assert_called_once()


@mock.patch.object(ChurchDAO, "get_church")
def test_delete_church_missing(mock_get_church):
    service = _build_service()
    mock_get_church.return_value = None

    with pytest.raises(NoChurchExists):
        service.delete_church()


@mock.patch.object(MediaService, "get_media_item_by_id")
@mock.patch.object(ChurchDAO, "get_church")
def test_get_church_logo(mock_get_church, mock_get_media_item):
    service = _build_service()
    logo = media_models.MediaItem(id=7, store="local", address="logo.png", created=datetime.now())
    church = models.Church(id=1, name="X", created=datetime.now())
    church.logo_image = logo
    mock_get_church.return_value = church
    mock_get_media_item.return_value = "file-response"

    assert service.get_church_logo() == "file-response"
    mock_get_media_item.assert_called_once_with(7, as_attachment=False)


@mock.patch.object(ChurchDAO, "get_church")
def test_get_church_logo_no_church(mock_get_church):
    service = _build_service()
    mock_get_church.return_value = None

    with pytest.raises(NoChurchExists):
        service.get_church_logo()


@mock.patch.object(ChurchDAO, "get_church")
def test_get_church_logo_without_logo(mock_get_church):
    service = _build_service()
    church = models.Church(id=1, name="X", created=datetime.now())
    church.logo_image = None
    mock_get_church.return_value = church

    assert service.get_church_logo() is None
