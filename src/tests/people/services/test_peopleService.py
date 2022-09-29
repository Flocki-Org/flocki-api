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
from src.app.people.models.people import FullViewPerson, UpdatePerson, SocialMediaLink
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.peopleService import PeopleService, NoPersonException
from src.app.people.models.database import models
from pytest_unordered import unordered


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


@mock.patch.object(PeopleDAO, 'get_person_by_id')
def test_update_person_person_not_found(mock_get_person_by_id):
    peopleDAO = PeopleDAO()
    people_service = PeopleService(peopleDAO=peopleDAO)

    mock_get_person_by_id.return_value = None

    with pytest.raises(NoPersonException):
        people_service.update_person(1, UpdatePerson(id=1, first_name="John", last_name="Smith"))



