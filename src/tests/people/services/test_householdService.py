from unittest import mock
from unittest.mock import call, ANY

import pytest
from fastapi import UploadFile
from starlette.responses import FileResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models as media_models
from src.app.media.services.mediaService import NoImageException, MediaService
from src.app.people.daos.householdDAO import HouseholdDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.models.database import models
from src.app.people.models.database.models import HouseholdImage
from src.app.people.models.household import ViewHousehold, CreateHousehold
from src.app.people.models.people import BasicViewPerson, ViewAddress
from src.app.people.services.householdService import HouseholdService, NoHouseholdException
from src.app.people.services.peopleService import NoPersonException


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_all_households')
def test_get_all_households_none(mock_get_all_households, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())
    mock_get_all_households.return_value = []
    mock_createHouseholdFromHouseholdEntity.return_value = []

    households = household_service.get_all_households()
    assert households == []
    assert mock_get_all_households.call_count == 1
    assert mock_createHouseholdFromHouseholdEntity.call_count == 0


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_all_households')
def test_get_all_households_some(mock_get_all_households, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())
    household_entity_1 = models.Household(id=1, leader_id=1, address_id=1)
    household_entity_2 = models.Household(id=2, leader_id=2, address_id=2)
    mock_get_all_households.return_value = [household_entity_1, household_entity_2]

    household_1 = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))
    household_2 = ViewHousehold(id=2, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))

    def side_effect(household_entity):
        if household_entity.id == 1:
            return household_1
        elif household_entity.id == 2:
            return household_2

    mock_createHouseholdFromHouseholdEntity.side_effect = side_effect

    households = household_service.get_all_households()
    assert households == [household_1, household_2]
    assert mock_get_all_households.call_count == 1
    assert mock_createHouseholdFromHouseholdEntity.call_count == 2
    mock_createHouseholdFromHouseholdEntity.assert_has_calls(
        [call(household_entity=household_entity_1), call(household_entity=household_entity_2)], any_order=True)


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_by_id_none(mock_get_household_by_id, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())
    mock_get_household_by_id.return_value = None

    with pytest.raises(NoHouseholdException):
        household = household_service.get_household_by_id(1)


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_by_id_one(mock_get_household_by_id, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())
    household_entity = models.Household(id=1, leader_id=1, address_id=1)
    mock_get_household_by_id.return_value = household_entity
    household = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))
    mock_createHouseholdFromHouseholdEntity.return_value = household

    household = household_service.get_household_by_id(1)
    assert household == household
    assert mock_get_household_by_id.call_count == 1
    assert mock_createHouseholdFromHouseholdEntity.call_count == 1
    mock_createHouseholdFromHouseholdEntity.assert_called_once_with(household_entity, include_household_image=True)


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'add_household')
@mock.patch.object(HouseholdFactory, 'createHouseholdEntityFromHousehold')
@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_add_household(mock_get_person_by_id, mock_get_image_by_id, mock_createHouseholdEntityFromHousehold,
                       mock_add_household,
                       mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory(),
                                         media_DAO=MediaDAO(), peopleDAO=PeopleDAO())

    household = CreateHousehold(id=1, leader_id=1, address_id=1, people_ids=[1, 2], household_image_id=1)
    people_list = [models.Person(id=1), models.Person(id=2)]
    household_entity = models.Household(id=1, leader_id=1, address_id=1, people=people_list)

    def mock_get_person_by_id_side_effect(person_id):
        if person_id == 1:
            return people_list[0]
        elif person_id == 2:
            return people_list[1]

    mock_get_person_by_id.side_effect = mock_get_person_by_id_side_effect

    image_entity = media_models.Image(id=1)
    mock_get_image_by_id.return_value = image_entity

    mock_createHouseholdEntityFromHousehold.return_value = household_entity
    mock_add_household.return_value = household_entity
    mock_createHouseholdFromHouseholdEntity.return_value = household

    household = household_service.add_household(household)

    assert household == household
    assert mock_createHouseholdEntityFromHousehold.call_count == 1
    assert mock_add_household.call_count == 1
    assert mock_createHouseholdFromHouseholdEntity.call_count == 1
    mock_get_person_by_id.assert_has_calls([call(1), call(2)], any_order=True)
    mock_createHouseholdEntityFromHousehold.assert_called_once_with(household, people_list)
    mock_add_household.assert_called_once_with(household_entity, image_entity)
    mock_createHouseholdFromHouseholdEntity.assert_called_once_with(household_entity, True)


@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_add_household_some_people_not_found(mock_get_person_by_id):
    household_service = HouseholdService(peopleDAO=PeopleDAO())

    household = CreateHousehold(id=1, leader_id=1, address_id=1, people_ids=[1, 2, 3, 4, 5], household_image_id=1)
    people_list = [models.Person(id=1), models.Person(id=2)]
    models.Household(id=1, leader_id=1, address_id=1, people=people_list)

    def mock_get_person_by_id_side_effect(person_id):
        if person_id == 1:
            return people_list[0]
        elif person_id == 2:
            return people_list[1]
        else:
            return None

    mock_get_person_by_id.side_effect = mock_get_person_by_id_side_effect

    with pytest.raises(NoPersonException) as e:
        household_service.add_household(household)

    assert e.value.args[0] == 'No people with the following IDs: [3, 4, 5]'
    mock_get_person_by_id.assert_has_calls([call(1), call(2), call(3), call(4), call(5)], any_order=True)


@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_add_household_no_image(mock_get_person_by_id, mock_get_image_by_id):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory(),
                                         media_DAO=MediaDAO(), peopleDAO=PeopleDAO())

    household = CreateHousehold(id=1, leader_id=1, address_id=1, people_ids=[1, 2], household_image_id=1)
    people_list = [models.Person(id=1), models.Person(id=2)]
    models.Household(id=1, leader_id=1, address_id=1, people=people_list)

    def mock_get_person_by_id_side_effect(person_id):
        if person_id == 1:
            return people_list[0]
        elif person_id == 2:
            return people_list[1]

    mock_get_person_by_id.side_effect = mock_get_person_by_id_side_effect

    mock_get_image_by_id.return_value = None

    with pytest.raises(NoImageException) as e:
        household_service.add_household(household)

    assert e.value.args[0] == 'No image with that ID: 1'


@mock.patch.object(HouseholdFactory, 'create_household_image_list_from_entity_list')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_images_by_household_id(mock_get_household_by_id,
                                              mock_create_household_image_list_from_entity_list):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    household = CreateHousehold(id=1, leader_id=1, address_id=1, people_ids=[1, 2], household_image_id=1)
    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity

    household = household_service.get_household_images_by_household_id(1)

    assert household == household
    assert mock_get_household_by_id.call_count == 1
    mock_get_household_by_id.assert_called_once_with(1)
    mock_create_household_image_list_from_entity_list.assert_called_once_with(household_entity)


@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_images_by_household_id_household_not_found(mock_get_household_by_id):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    mock_get_household_by_id.return_value = None
    with pytest.raises(NoHouseholdException) as e:
        household_service.get_household_images_by_household_id(1)

    assert e.value.args[0] == 'No household with that ID: 1'


@mock.patch.object(MediaFactory, 'create_image_from_image_entity')
@mock.patch.object(HouseholdDAO, 'add_household_image')
@mock.patch.object(MediaService, 'upload_image')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_upload_household_image(mock_get_household_by_id, mock_upload_image, mock_add_household_image,
                                mock_create_image_from_image_entity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), media_service=MediaService(),
                                         media_factory=MediaFactory())

    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity
    file = UploadFile(filename="test.jpg", content_type="image/jpeg")
    file.content_type = "image/jpeg"
    description = f"Profile image for household with ID: {household_entity.id}"
    image_entity = media_models.Image(id=1, description=description)
    mock_upload_image.return_value = image_entity

    household = household_service.upload_household_image(1, file)

    assert household == household
    assert mock_get_household_by_id.call_count == 1
    assert mock_upload_image.call_count == 1
    assert mock_add_household_image.call_count == 1
    assert mock_create_image_from_image_entity.call_count == 1
    mock_get_household_by_id.assert_called_once_with(1)
    mock_upload_image.assert_called_once_with(file, ANY, description)
    mock_add_household_image.assert_called_once_with(household_entity, image_entity)
    mock_create_image_from_image_entity.assert_called_once_with(image_entity)


@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_upload_household_image_no_household(mock_get_household_by_id):
    household_service = HouseholdService(household_DAO=HouseholdDAO())

    models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = None
    with pytest.raises(NoHouseholdException) as e:
        household_service.upload_household_image(1, UploadFile(filename="test.jpg", content_type="image/jpeg"))

    assert e.value.args[0] == 'No household with that ID: 1'


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_image_by_household_id(mock_get_household_by_id, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity
    household_view = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))
    image = media_models.Image(id=1, store="local", address="test.jpg")
    household_view.household_image = image
    mock_createHouseholdFromHouseholdEntity.return_value = household_view

    file_response: FileResponse = household_service.get_household_image_by_household_id(1)

    assert file_response.path == "test.jpg"
    assert mock_get_household_by_id.call_count == 1
    mock_get_household_by_id.assert_called_once_with(1)
    mock_createHouseholdFromHouseholdEntity.assert_called_once_with(household_entity, True)


@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_image_by_household_id_no_household(mock_get_household_by_id):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    mock_get_household_by_id.return_value = None
    with pytest.raises(NoHouseholdException) as e:
        household_service.get_household_image_by_household_id(1)

    assert e.value.args[0] == 'No household with that ID: 1'


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_image_by_household_id_none_view_household(mock_get_household_by_id,
                                                                 mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity
    mock_createHouseholdFromHouseholdEntity.return_value = None

    file_response: FileResponse = household_service.get_household_image_by_household_id(1)

    assert file_response is None


@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_image_by_household_id_none_image(mock_get_household_by_id, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity
    mock_createHouseholdFromHouseholdEntity.return_value = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))

    file_response: FileResponse = household_service.get_household_image_by_household_id(1)

    assert file_response is None



@mock.patch.object(HouseholdFactory, 'createHouseholdFromHouseholdEntity')
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_get_household_image_by_household_id_s3_not_implemented(mock_get_household_by_id, mock_createHouseholdFromHouseholdEntity):
    household_service = HouseholdService(household_DAO=HouseholdDAO(), household_factory=HouseholdFactory())

    household_entity = models.Household(id=1, leader_id=1, address_id=1)

    mock_get_household_by_id.return_value = household_entity
    household_view = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))
    image = media_models.Image(id=1, store="s3", address="test.jpg")
    household_view.household_image = image
    mock_createHouseholdFromHouseholdEntity.return_value = household_view

    with pytest.raises(NotImplementedError) as e:
        household_service.get_household_image_by_household_id(1)

    e.value.args[0] == 'S3 not implemented yet'


