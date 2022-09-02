from src.app.people.services.householdUtils import HouseholdUtils

def test_get_household_ids_to_remove_remove_one():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3, 4]
    new_household_ids = [1, 2, 3]
    assert household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids) == [4]

def test_get_household_ids_to_remove_remove_none():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3, 4]
    new_household_ids = [1, 2, 3, 4]
    assert household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids) == []

def test_get_household_ids_to_remove_remove_all():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3, 4]
    new_household_ids = [5, 6, 7, 8]
    assert household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids) == [1, 2, 3, 4]

def test_get_household_ids_to_remove_remove_some():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3, 4]
    new_household_ids = [1, 2]
    assert household_utils.get_household_ids_to_remove(existing_household_ids, new_household_ids) == [3, 4]

def test_get_household_ids_to_add_add_one():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3]
    new_household_ids = [1, 2, 3, 5]
    assert household_utils.get_household_ids_to_add(existing_household_ids, new_household_ids) == [5]

def test_get_household_ids_to_add_add_none():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3]
    new_household_ids = [1, 2, 3]
    assert household_utils.get_household_ids_to_add(existing_household_ids, new_household_ids) == []

def test_get_household_ids_to_add_add_all():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3]
    new_household_ids = [5, 6, 7, 8]
    assert household_utils.get_household_ids_to_add(existing_household_ids, new_household_ids) == [5, 6, 7, 8]

def test_get_household_ids_to_add_add_some():
    household_utils = HouseholdUtils()
    existing_household_ids = [1, 2, 3]
    new_household_ids = [1, 2, 5, 7]
    assert household_utils.get_household_ids_to_add(existing_household_ids, new_household_ids) == [5, 7]