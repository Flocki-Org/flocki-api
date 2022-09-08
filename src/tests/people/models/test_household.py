import pytest

from src.app.people.models.household import CreateHousehold
from pydantic import ValidationError

def test_create_household_model():
    household = CreateHousehold(
        address_id=1,
        people_ids=[1, 2, 3],
        leader_id=1,
        household_image_id=1)
    assert household is not None

def test_create_household_model_with_invalid_leader_id():
    #should throw an exception

    with pytest.raises(ValidationError) as e:
        CreateHousehold(
            address_id=1,
            people_ids=[1, 2, 3],
            leader_id=5,
            household_image_id=1)

    assert e is not None

def test_create_household_model_with_no_leader_id():
    #should throw an exception

    with pytest.raises(ValidationError) as e:
        CreateHousehold(
            address_id=1,
            people_ids=[1, 2, 3],
            household_image_id=1)

    assert e is not None