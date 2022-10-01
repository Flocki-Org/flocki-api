import datetime

import pytest
from fastapi.responses import FileResponse

from unittest import mock
from unittest.mock import call

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.models.media import ViewImage
from src.app.media.models.database import models as media_models
from src.app.media.services.mediaService import NoImageException
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.household import ViewHousehold
from src.app.people.models.people import FullViewPerson, UpdatePerson, SocialMediaLink, CreatePerson, Gender, \
    MaritalStatus, ViewAddress, BasicViewPerson
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.householdUtils import HouseholdUtils
from src.app.people.services.peopleService import PeopleService, NoPersonException, \
    NoHouseholdExceptionForPersonCreation, UnableToRemoveLeaderFromHouseholdException
from src.app.people.models.database import models
from pytest_unordered import unordered
from src.app.people.daos.householdDAO import HouseholdDAO
from src.app.utils.DateUtils import DateUtils


@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_all')
def test_get_all(mock_get_all, mock_create_person_from_person_entity):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory)
    person_1 = models.Person(id=1, first_name="John")
    person_2 = models.Person(id=2, first_name="Jane")
    person_3 = models.Person(id=3, first_name="Jimmy")
    mock_get_all.return_value = [person_1, person_2, person_3]

    full_view_person_1 = FullViewPerson(id=1, first_name='John')
    full_view_person_2 = FullViewPerson(id=2, first_name='Jane')
    full_view_person_3 = FullViewPerson(id=3, first_name='Jimmy')

    def side_effect(person_entity: models.Person, include_profile_image=True, include_households=True) -> FullViewPerson:
        if person_entity.id == 1:
            return full_view_person_1
        elif person_entity.id == 2:
            return full_view_person_2
        elif person_entity.id == 3:
            return full_view_person_3

    mock_create_person_from_person_entity.side_effect = side_effect

    people = people_service.get_all()
    # for some reason the order of parameters matters, and is reversed to what is actually passed in, in the code.
    calls = [call(include_households=True, include_profile_image=True, person_entity=person_1),
             call(include_households=True, include_profile_image=True, person_entity=person_2),
             call(include_households=True, include_profile_image=True, person_entity=person_3)]
    mock_create_person_from_person_entity.assert_has_calls(calls, any_order=True)
                                                                #call(person_2, include_profile_image=True, include_households=True),
                                                                #call(person_3, include_profile_image=True, include_households=True)])

    assert len(people) == 3
    assert people == unordered([full_view_person_1, full_view_person_2, full_view_person_3])

@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_by_id(mock_get_person_by_id, mock_create_person_from_person_entity):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory)
    person_1 = models.Person(id=1, first_name="John")

    mock_get_person_by_id.return_value = [person_1]
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name='John')
    person = people_service.get_by_id(1)
    assert person is not None
    assert person.id == 1
    assert person.first_name == "John"


@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_profile_image_by_person_id_store_local(mock_get_person_by_id, mock_create_person_from_person_entity, mock_get_image_by_id):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, media_DAO=mediaDAO)
    person_1 = models.Person(id=1, first_name="John")

    mock_get_person_by_id.return_value = [person_1]
    view_image = ViewImage(id=1)
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name='John', profile_image=view_image)
    mock_get_image_by_id.return_value = media_models.Image(id=1, store="local", address="path/to/image.jpg")
    fileResponse: FileResponse = people_service.get_profile_image_by_person_id(1)

    assert fileResponse.path == "path/to/image.jpg"


@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_profile_image_by_person_id_store_none(mock_get_person_by_id, mock_create_person_from_person_entity, mock_get_image_by_id):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, media_DAO=mediaDAO)
    person_1 = models.Person(id=1, first_name="John")

    mock_get_person_by_id.return_value = [person_1]
    view_image = ViewImage(id=1)
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name='John', profile_image=view_image)
    mock_get_image_by_id.return_value = media_models.Image(id=1, store=None, address="path/to/image.jpg")
    fileResponse: FileResponse = people_service.get_profile_image_by_person_id(1)

    assert fileResponse == None

@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_profile_image_by_person_id_store_none(mock_get_person_by_id, mock_create_person_from_person_entity, mock_get_image_by_id):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, media_DAO=mediaDAO)
    person_1 = models.Person(id=1, first_name="John")

    mock_get_person_by_id.return_value = [person_1]
    view_image = ViewImage(id=1)
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name='John', profile_image=view_image)
    mock_get_image_by_id.return_value = media_models.Image(id=1, store="s3", address="path/to/image.jpg")
    with pytest.raises(NotImplementedError) as e:
        people_service.get_profile_image_by_person_id(1)

    assert e is not None

@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_profile_image_by_person_id_person_none(mock_get_person_by_id, mock_create_person_from_person_entity, mock_get_image_by_id):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, media_DAO=mediaDAO)

    mock_get_person_by_id.return_value = None

    with pytest.raises(NoPersonException) as e:
        people_service.get_profile_image_by_person_id(1)

    assert e is not None

@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_get_profile_image_by_person_id_store_none(mock_get_person_by_id, mock_create_person_from_person_entity, mock_get_image_by_id):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, media_DAO=mediaDAO)
    person_1 = models.Person(id=1, first_name="John")

    mock_get_person_by_id.return_value = [person_1]
    mock_create_person_from_person_entity.return_value = None
    response = people_service.get_profile_image_by_person_id(1)

    assert response == None

#TODO test update person

@mock.patch.object(MediaDAO, 'get_image_by_id')
def test_validate_image_id_invalid(mock_get_image_by_id):
    mediaDAO = MediaDAO()
    people_service = PeopleService( media_DAO=mediaDAO)
    mock_get_image_by_id.return_value = None
    with pytest.raises(NoImageException) as e:
        people_service.validate_image_id(1)

    assert e is not None

@mock.patch.object(MediaDAO, 'get_image_by_id')
def test_validate_image_id_valid(mock_get_image_by_id):
    mediaDAO = MediaDAO()
    people_service = PeopleService( media_DAO=mediaDAO)
    mock_get_image_by_id.return_value = media_models.Image(id=1, store="local", address="path/to/image.jpg")

    people_service.validate_image_id(1)

    # no exception has been raised. test passes

@mock.patch.object(AddressDAO, 'get_address_by_id')
def test_validate_addresses_invalid(mock_get_address_by_id):
    addressDAO = AddressDAO()
    people_service = PeopleService(addressDAO=addressDAO)
    mock_get_address_by_id.return_value = None
    with pytest.raises(NoAddressException) as e:
        people_service.validate_addresses([1])

    assert e is not None


@mock.patch.object(AddressDAO, 'get_address_by_id')
def test_validate_addresses_valid(mock_get_address_by_id):
    addressDAO = AddressDAO()
    people_service = PeopleService(addressDAO=addressDAO)
    mock_get_address_by_id.return_value = models.Address(id=1)

    people_service.validate_addresses([1])

    # no exception has been raised. test passes

#TODO the update person test can be expanded to test a lot more of its paths. But for now, this will do.

@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch('src.app.people.services.peopleService.PeopleService.update_households_for_person')
@mock.patch.object(PeopleDAO, 'update_person')
@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch.object(AddressDAO, 'delete_address')
@mock.patch.object(AddressDAO, 'create_address_linked_to_person')
@mock.patch.object(AddressDAO, 'get_address_by_id')
@mock.patch.object(AddressDAO, 'get_existing_addresses_for_person')
@mock.patch.object(PeopleDAO, 'create_social_media_link')
@mock.patch.object(PeopleDAO, 'delete_social_media_link')
@mock.patch.object(PeopleDAO, 'get_existing_social_media_links')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_image_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_household_remove_person')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person(mock_get_person_by_id, mock_validate_households, mock_validate_household_remove_person, mock_validate_addresses,
                       mock_validate_image_id, mock_get_existing_social_media_links, mock_delete_social_media_link, mock_create_social_media_link,
                       mock_get_existing_addresses_for_person, mock_get_address_by_id, mock_create_address_linked_to_person,
                       mock_delete_address, mock_get_image_by_id, mock_update_person, mock_update_households_for_person,
                       mock_create_person_from_person_entity):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    addressDAO = AddressDAO()
    mediaDAO = MediaDAO()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory, addressDAO=addressDAO, media_DAO=mediaDAO)
    existing_person = models.Person(id=1, first_name="John")
    existing_person.social_media_links = [models.SocialMediaLink(id=1, person_id=1, type="facebook", url="facebook.com/john")]
    existing_person.households = [models.Household(id=1, leader_id=5), models.Household(id=2, leader_id=5)]

    home_address = models.Address(
        id=1,
        type="home",
    )

    business_address = models.Address(
        id=2,
        type="business",
    )
    people_address_home = models.PeopleAddress(id=1, person_id=existing_person.id, address=home_address)
    people_address_business = models.PeopleAddress(id=2, person_id=existing_person.id, address=business_address)
    existing_person.addresses = [people_address_home, people_address_business]

    new_address = models.Address(
        id=3,
        type="home",
    )

    update_person = UpdatePerson(id=1, first_name="John", last_name="Smith")

    update_person.addresses = [3]
    update_person.social_media_links = [SocialMediaLink(type="facebook", url="http://facebook.com/john")]
    update_person.profile_image_id = 1
    updated_household_ids = [3,4]
    update_person.household_ids = updated_household_ids

    mock_get_person_by_id.return_value = existing_person
    mock_validate_households.return_value = None
    mock_validate_household_remove_person.return_value = None
    mock_validate_addresses.return_value = None
    mock_validate_image_id.return_value = None

    mock_get_existing_social_media_links.return_value = existing_person.social_media_links
    mock_get_address_by_id.return_value = new_address
    mock_create_address_linked_to_person.return_value = None

    mock_delete_social_media_link.return_value = None
    mock_create_social_media_link.return_value = None
    mock_get_existing_addresses_for_person.return_value = existing_person.addresses
    mock_delete_address.return_value = None
    mock_create_address_linked_to_person.return_value = None
    image_entity = media_models.Image(id=1, store="local", address="path/to/image.jpg")
    mock_get_image_by_id.return_value = image_entity
    mock_update_person.return_value = None
    mock_update_households_for_person.return_value = None
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name="John", last_name="Smith")

    people_service.update_person(update_person.id, update_person)

    mock_validate_households.assert_called_with(updated_household_ids)
    mock_validate_household_remove_person.assert_called_with(updated_household_ids, existing_person)
    mock_validate_addresses.assert_called_with(update_person.addresses)
    mock_validate_image_id.assert_called_with(update_person.profile_image_id)
    mock_delete_social_media_link.assert_has_calls([call(1)])
    mock_create_social_media_link.assert_has_calls([call(1, "facebook", "http://facebook.com/john")])
    mock_delete_address.assert_has_calls([call(1), call(2)])
    mock_create_address_linked_to_person.assert_has_calls([call(new_address, existing_person)])
    update_values = update_person.dict()
    update_values.pop('household_ids')
    update_values.pop('social_media_links')
    update_values.pop('addresses')
    update_values.pop('profile_image_id')

    mock_update_person.assert_called_with(1, update_values, image_entity)
    mock_update_households_for_person.assert_has_calls([call(updated_household_ids, existing_person)])
    mock_create_person_from_person_entity.call_count == 1


@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_not_found(mock_get_person_by_id):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)

    mock_get_person_by_id.return_value = None

    with pytest.raises(NoPersonException):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_invalid_household_provided(mock_get_person_by_id, mock_validate_households):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)
    existing_person = models.Person(id=1, first_name="John")
    mock_get_person_by_id.return_value = existing_person

    # mock validate households to raise an exception
    mock_validate_households.side_effect = NoHouseholdExceptionForPersonCreation

    with pytest.raises(NoHouseholdExceptionForPersonCreation):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_household_remove_person')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_unable_to_remove_person_from_household(mock_get_person_by_id, mock_validate_households,
                                                                     mock_validate_household_remove_person):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)
    existing_person = models.Person(id=1, first_name="John")
    mock_get_person_by_id.return_value = existing_person

    # mock validate households to raise an exception
    mock_validate_households.return_value = None
    mock_validate_household_remove_person.side_effect = UnableToRemoveLeaderFromHouseholdException

    with pytest.raises(UnableToRemoveLeaderFromHouseholdException):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_household_remove_person')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_unable_to_remove_person_from_household(mock_get_person_by_id, mock_validate_households,
                                                                     mock_validate_household_remove_person, mock_validate_addresses):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)
    existing_person = models.Person(id=1, first_name="John")
    mock_get_person_by_id.return_value = existing_person

    # mock validate households to raise an exception
    mock_validate_households.return_value = None
    mock_validate_household_remove_person.return_value = None
    mock_validate_addresses.side_effect = NoAddressException

    with pytest.raises(NoAddressException):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_image_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_household_remove_person')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_unable_to_remove_person_from_household(mock_get_person_by_id, mock_validate_households,
                                                                     mock_validate_household_remove_person, mock_validate_addresses,
                                                                     mock_validate_image_id):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)
    existing_person = models.Person(id=1, first_name="John")
    mock_get_person_by_id.return_value = existing_person

    # mock validate households to raise an exception
    mock_validate_households.return_value = None
    mock_validate_household_remove_person.return_value = None
    mock_validate_addresses.return_value = None
    mock_validate_image_id.side_effect = NoImageException("Image with id: 1 does not exist")
    with pytest.raises(NoImageException):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith", profile_image_id=1))

@mock.patch.object(MediaDAO, 'get_image_by_id')
def test_validate_image_id(mock_get_image_by_id):
    mediaDAO = MediaDAO()
    people_service = PeopleService(media_DAO=mediaDAO)
    mock_get_image_by_id.return_value = None
    with pytest.raises(NoImageException):
        people_service.validate_image_id(1)


@mock.patch.object(AddressDAO, 'get_address_by_id')
def test_validate_addresses(mock_get_address_by_id):
    addressDAO = AddressDAO()
    people_service = PeopleService(addressDAO=addressDAO)
    mock_get_address_by_id.return_value = None
    with pytest.raises(NoAddressException):
        people_service.validate_addresses([1])


@mock.patch.object(HouseholdDAO, 'get_household_by_id')
@mock.patch.object(HouseholdDAO, 'remove_person_from_household')
@mock.patch.object(HouseholdDAO, 'add_person_to_household')
@mock.patch.object(HouseholdUtils, 'get_household_ids_to_remove')
@mock.patch.object(HouseholdUtils, 'get_household_ids_to_add')
@mock.patch.object(HouseholdUtils, 'get_existing_household_ids')
def test_update_households_for_persons(mock_get_existing_household_ids, mock_get_household_ids_to_add, mock_get_household_ids_to_remove,
                                       mock_add_person_to_household, mock_remove_person_from_household, mock_get_household_by_id):
    householdUtils = HouseholdUtils()
    householdDAO = HouseholdDAO()
    people_service = PeopleService(household_utils=householdUtils, household_DAO=householdDAO)
    mock_get_existing_household_ids.return_value = [1, 2]
    mock_get_household_ids_to_add.return_value = [3]
    mock_get_household_ids_to_remove.return_value = [1]
    household_1 = models.Household(id=1, leader_id=1)
    household_3 = models.Household(id=3, leader_id=2)
    def side_effect(household_id):
        if(household_id == 1):
            return household_1
        elif(household_id == 3):
            return household_3

    mock_get_household_by_id.side_effect = side_effect

    #Person is not relevant in this call because of the mocking.
    person_entity = models.Person(id=1)
    people_service.update_households_for_person([2, 3], person_entity)

    mock_get_household_by_id.assert_has_calls([call(1), call(3)], any_order=True)
    mock_add_person_to_household.assert_called_once_with(household_3, person_entity)
    mock_remove_person_from_household.assert_called_once_with(household_1, person_entity)


# The fact that this test is so complicated or at least long, is a sign that the method should be refactored. There is
# no complex logic, but just a lot of things happening in the one method. The test mocks almost everything making it a little
# less valuable.
@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'create_person')
@mock.patch.object(PeopleDAO, 'get_person_by_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.add_person_to_households')
@mock.patch.object(DateUtils, 'get_current_datetime')
@mock.patch.object(PeopleFactory, 'create_person_entity_from_create_person')
@mock.patch.object(AddressDAO, 'get_address_by_id')
@mock.patch.object(MediaDAO, 'get_image_by_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_image_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
def test_create_person(mock_validate_households, mock_validate_addresses, mock_validate_image_id, mock_get_image_by_id,
                       mock_get_address_by_id, mock_create_person_entity_from_create_person, mock_get_current_datetime,
                       mock_add_person_to_households, mock_get_person_by_id, mock_create_person, mock_create_person_from_person_entity):
    people_service = PeopleService(peopleDAO=PeopleDAO(), addressDAO=AddressDAO(), media_DAO=MediaDAO(), people_factory=PeopleFactory())


    new_person = CreatePerson(first_name="John", last_name="Smith", email="john.smith@test.com", mobile_number="07212345678",
                              date_of_birth= datetime.date(1980, 1, 1), gender=Gender.male, marriage_date=datetime.date(2010, 1, 1),
                              social_media_links=[SocialMediaLink(url="https://www.facebook.com/1", type="facebook"),
                               SocialMediaLink(url="https://www.instagram.com/1", type="instagram")],
                              marital_status=MaritalStatus.married, profile_image_id=1, addresses=[1,2], household_ids=[1, 2])
    #no validation errors
    mock_validate_households.return_value = None
    mock_validate_addresses.return_value = None
    mock_validate_image_id.return_value = None
    image_to_link = media_models.Image(id=1)
    mock_get_image_by_id.return_value = image_to_link
    home_address = models.Address(
        id=1,
        type="home",
    )
    business_address = models.Address(
        id=2,
        type="business",
    )
    def side_effect(address_id):
        if(address_id == 1):
            return home_address
        elif(address_id == 2):
            return business_address
    mock_get_address_by_id.side_effect = side_effect

    people_address_home = models.PeopleAddress(person_id=1, address=home_address)
    people_address_business = models.PeopleAddress(person_id=1, address=business_address)
    create_entity = models.Person(
        first_name="John", last_name="Smith", email="john.smith@test.com", mobile_number="07212345678",
        date_of_birth=datetime.date(1980, 1, 1), gender=Gender.male, marriage_date=datetime.date(2010, 1, 1),
        social_media_links=[models.SocialMediaLink(url="https://www.facebook.com/1", type="facebook"),
                               models.SocialMediaLink(url="https://www.instagram.com/1", type="instagram")],
        marital_status=MaritalStatus.married, addresses=[people_address_home, people_address_business])
    mock_create_person_entity_from_create_person.return_value = create_entity

    now = datetime.datetime.now()
    mock_get_current_datetime.return_value = now

    people_address_home_created = models.PeopleAddress(id=1, address=home_address)
    people_address_business_created = models.PeopleAddress(id=2, address=business_address)
    created_person = models.Person(id=1,
        first_name="John", last_name="Smith", email="john.smith@test.com", mobile_number="07212345678",
        date_of_birth=datetime.date(1980, 1, 1), gender=Gender.male, marriage_date=datetime.date(2010, 1, 1),
        social_media_links=[models.SocialMediaLink(id=1, url="https://www.facebook.com/1", type="facebook"),
                               models.SocialMediaLink(id=2, url="https://www.instagram.com/1", type="instagram")],
        marital_status=MaritalStatus.married, addresses=[people_address_home_created, people_address_business_created])
    mock_create_person.return_value = created_person

    mock_add_person_to_households.return_value = None
    mock_get_person_by_id.return_value = created_person
    mock_create_person_from_person_entity.return_value = FullViewPerson(id=1, first_name="John", last_name="Smith", email="john.smith@test.com", mobile_number="07212345678",
                              date_of_birth= datetime.date(1980, 1, 1), gender=Gender.male, marriage_date=datetime.date(2010, 1, 1),
                              social_media_links=[SocialMediaLink(url="https://www.facebook.com/1", type="facebook"),
                              SocialMediaLink(url="https://www.instagram.com/1", type="instagram")], registered_date=now,
                              marital_status=MaritalStatus.married, profile_image_id=1, addresses=[ViewAddress(id=1),ViewAddress(id=2)],
                              household_ids=[ViewHousehold(id=1, leader=BasicViewPerson(id=1),address=ViewAddress(id=1)),
                                             ViewHousehold(id=2, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))])


    new_created_person = people_service.create_person(new_person)

    mock_validate_households.assert_called_once()
    mock_validate_addresses.assert_called_once()
    mock_validate_image_id.assert_called_once()
    mock_get_image_by_id.assert_called_once()
    assert mock_get_address_by_id.call_count == 2
    mock_create_person_entity_from_create_person.assert_called_once()
    mock_get_current_datetime.assert_called_once()
    mock_add_person_to_households.assert_called_once()
    mock_create_person.assert_called_once()
    mock_create_person.assert_called_with(create_entity, image_to_link)
    mock_create_person_from_person_entity.assert_called_once()
    mock_add_person_to_households.assert_called_once()
    mock_add_person_to_households.assert_called_with(created_person, [1,2])
    mock_get_person_by_id.assert_called_once()
    mock_get_person_by_id.assert_called_with(1)
    mock_create_person_from_person_entity.assert_called_with(created_person, include_households=True, include_profile_image=True)
    assert new_created_person.registered_date == now.date()

@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
def test_create_person_invalid_household_provided(mock_validate_households):
    people_service = PeopleService()

    mock_validate_households.side_effect = NoHouseholdExceptionForPersonCreation

    with pytest.raises(NoHouseholdExceptionForPersonCreation):
        people_service.create_person(CreatePerson(first_name="John", last_name="Smith", email="test@test.com", mobile_number="07212345678"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
def test_create_person_invalid_addresses_provided(mock_validate_households, mock_validate_addresses):
    people_service = PeopleService()

    mock_validate_households.return_value = None
    mock_validate_addresses.side_effect = NoAddressException

    with pytest.raises(NoAddressException):
        people_service.create_person(CreatePerson(first_name="John", last_name="Smith", email="test@test.com", mobile_number="07212345678"))


@mock.patch('src.app.people.services.peopleService.PeopleService.validate_image_id')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_addresses')
@mock.patch('src.app.people.services.peopleService.PeopleService.validate_households')
def test_create_person_invalid_image_id_provided(mock_validate_households, mock_validate_addresses, mock_validate_image_id):
    people_service = PeopleService()
    mock_validate_households.return_value = None
    mock_validate_addresses.return_value=None
    mock_validate_image_id.side_effect = NoImageException("No image with id 1")

    with pytest.raises(NoImageException):
        people_service.create_person(CreatePerson(first_name="John", last_name="Smith", email="test@test.com", mobile_number="07212345678"))


#def validate_household_remove_person(self, new_household_ids, personToUpdate):
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
@mock.patch.object(HouseholdUtils, 'get_household_ids_to_remove')
@mock.patch.object(HouseholdUtils, 'get_existing_household_ids')
def test_validate_household_remove_person_valid(mock_get_existing_household_ids, mock_get_household_ids_to_remove, mock_get_household_by_id):
    people_service = PeopleService(household_DAO=HouseholdDAO(), household_utils=HouseholdUtils())

    mock_get_existing_household_ids.return_value = [1,2,3,4]
    mock_get_household_ids_to_remove.return_value = [3]
    mock_get_household_by_id.return_value = models.Household(id=3, leader=models.Person(id=2), address_id=1)

    people_service.validate_household_remove_person([1,2,3], models.Person(id=1))

    #no exception means test passed
    mock_get_existing_household_ids.assert_called_once()
    mock_get_household_ids_to_remove.assert_called_once()
    mock_get_household_by_id.assert_called_once()


#def validate_household_remove_person(self, new_household_ids, personToUpdate):
@mock.patch.object(HouseholdDAO, 'get_household_by_id')
@mock.patch.object(HouseholdUtils, 'get_household_ids_to_remove')
@mock.patch.object(HouseholdUtils, 'get_existing_household_ids')
def test_validate_household_remove_person(mock_get_existing_household_ids, mock_get_household_ids_to_remove, mock_get_household_by_id):
    people_service = PeopleService(household_DAO=HouseholdDAO(), household_utils=HouseholdUtils())

    mock_get_existing_household_ids.return_value = [1,2,3,4]
    mock_get_household_ids_to_remove.return_value = [3]
    mock_get_household_by_id.return_value = models.Household(id=3, leader=models.Person(id=1), address_id=1)

    with(pytest.raises(UnableToRemoveLeaderFromHouseholdException)):
        people_service.validate_household_remove_person([1,2,3], models.Person(id=1))

    #no exception means test passed
    mock_get_existing_household_ids.assert_called_once()
    mock_get_household_ids_to_remove.assert_called_once()
    mock_get_household_by_id.assert_called_once()

@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_validate_households(mock_get_household_by_id):
    people_service = PeopleService(household_DAO=HouseholdDAO(), household_utils=HouseholdUtils())

    mock_get_household_by_id.return_value = models.Household(id=1, leader=models.Person(id=1), address_id=1)

    people_service.validate_households([1])

    #no exception means test passed
    mock_get_household_by_id.assert_called_once()


@mock.patch.object(HouseholdDAO, 'get_household_by_id')
def test_validate_households(mock_get_household_by_id):
    people_service = PeopleService(household_DAO=HouseholdDAO(), household_utils=HouseholdUtils())

    mock_get_household_by_id.return_value = None
    with(pytest.raises(NoHouseholdExceptionForPersonCreation)):
        people_service.validate_households([1])

    mock_get_household_by_id.assert_called_once()
