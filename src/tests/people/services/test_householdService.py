from unittest import mock
from unittest.mock import call

import pytest

from src.app.people.daos.householdDAO import HouseholdDAO
from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.models.database import models
from src.app.people.models.household import ViewHousehold
from src.app.people.models.people import BasicViewPerson, ViewAddress
from src.app.people.services.householdService import HouseholdService, NoHouseholdException


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
    mock_createHouseholdFromHouseholdEntity.assert_has_calls([call(household_entity=household_entity_1), call(household_entity=household_entity_2)], any_order=True)


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
    mock_createHouseholdFromHouseholdEntity.assert_has_calls([call(household_entity, include_household_image=True)], any_order=True)

