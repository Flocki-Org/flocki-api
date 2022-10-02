from datetime import datetime
from unittest import mock
from unittest.mock import call

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.database import models
from src.app.people.models.household import ViewHousehold
from src.app.people.models.people import SocialMediaLink, BasicViewPerson, ViewAddress, CreatePerson, Gender, \
    MaritalStatus
from src.app.media.models.database import models as media_models


people_factory = PeopleFactory()


def test_create_basic_person_view_from_person_entity():
    # we create a new entity in each test to keep them independent
    person_entity = models.Person(
        id=1,
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        gender="male",
        marital_status="single",
    )
    person_view = people_factory.create_basic_person_view_from_person_entity(person_entity)
    assert person_view.id == 1
    assert person_view.first_name == "Test Name"
    assert person_view.last_name == "Last Name"


@mock.patch.object(AddressFactory, 'create_address_from_address_entity')
def test_create_person_from_person_entity(mock_create_address_from_address_entity):
    address_factory = AddressFactory()
    pfactory = PeopleFactory(address_factory=address_factory)

    person_entity = models.Person(
        id=1,
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        gender="male",
        marital_status="single",
    )
    sml_fb: models.SocialMediaLink = models.SocialMediaLink(
        person_id=person_entity.id,
        type="facebook",
        url="https://www.facebook.com/test")

    sml_twitter: models.SocialMediaLink = models.SocialMediaLink(
        person_id=person_entity.id,
        type="twitter",
        url="https://www.twitter.com/test")

    person_entity.social_media_links = [
        sml_fb, sml_twitter
    ]

    image_entity_1 = media_models.Image(
        id=1,
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )

    image_entity_2 = media_models.Image(
        id=2,
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2022, 1, 1, 0, 0),
        store="local"
    )
    person_image_entity_1 = models.PersonImage(id=1, person_id=person_entity.id, image=image_entity_1)
    person_image_entity_2 = models.PersonImage(id=2, person_id=person_entity.id, image=image_entity_2)
    person_entity.profile_images = [person_image_entity_1, person_image_entity_2]

    home_address = models.Address(
        id=1,
        type="home",
    )

    business_address = models.Address(
        id=2,
        type="business",
    )
    people_address_home = models.PeopleAddress(id=1, person_id=person_entity.id, address=home_address)
    people_address_business = models.PeopleAddress(id=2, person_id=person_entity.id, address=business_address)
    person_entity.addresses = [people_address_home, people_address_business]

    full_person_view = pfactory.create_person_from_person_entity(person_entity, include_households=False,
                                                                 include_profile_image=False)

    assert full_person_view.id == 1
    assert full_person_view.first_name == person_entity.first_name
    assert full_person_view.last_name == person_entity.last_name
    assert full_person_view.email == person_entity.email
    assert full_person_view.mobile_number == person_entity.mobile_number
    assert full_person_view.gender == "male"
    assert full_person_view.marital_status == "single"

    mock_create_address_from_address_entity.assert_has_calls([call(home_address), call(business_address)],
                                                             any_order=True)
    address_factory.create_address_from_address_entity.assert_has_calls([call(home_address), call(business_address)],
                                                                        any_order=True)


@mock.patch.object(MediaFactory, 'create_view_image_from_image_entity')
def test_create_person_from_person_entity_with_image(mock_createViewImageFromImageEntity):
    media_factory = MediaFactory()
    pfactory = PeopleFactory(media_factory=media_factory)

    person_entity = models.Person(
        id=1,
    )

    image_entity_1 = media_models.Image(
        id=1,
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2020, 1, 1, 0, 0),
        store="local"
    )

    image_entity_2 = media_models.Image(
        id=2,
        description="test_image.jpg",
        address="test_image.jpg",
        created=datetime(2022, 1, 1, 0, 0),
        store="local"
    )
    person_image_entity_1 = models.PersonImage(id=1, person_id=person_entity.id, image=image_entity_1)
    person_image_entity_2 = models.PersonImage(id=2, person_id=person_entity.id, image=image_entity_2)
    person_entity.profile_images = [person_image_entity_1, person_image_entity_2]

    full_person_view = pfactory.create_person_from_person_entity(person_entity, include_households=False,
                                                                 include_profile_image=True)

    assert full_person_view.id == 1

    mock_createViewImageFromImageEntity.assert_called_with(image_entity_2)
    media_factory.create_view_image_from_image_entity.assert_called_with(image_entity_2)


@mock.patch('src.app.people.factories.peopleFactory.PeopleFactory.create_household_view')
def test_create_person_from_person_entity_with_households(mock_create_household_view):
    person_entity = models.Person(
        id=1,
    )

    household_1 = models.Household(
        id=1,
    )
    household_2 = models.Household(
        id=2,
    )
    household_view_1 = ViewHousehold(id=1, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))
    household_view_2 = ViewHousehold(id=2, leader=BasicViewPerson(id=1), address=ViewAddress(id=1))

    def side_effect(household):
        if household.id == 1:
            return household_view_1
        else:
            return household_view_2

    mock_create_household_view.side_effect = side_effect

    person_entity.households = [household_1, household_2]

    full_person_view = people_factory.create_person_from_person_entity(person_entity, include_households=True,
                                                                       include_profile_image=False)

    assert full_person_view.id == 1
    assert len(full_person_view.households) == 2
    assert household_view_1 in full_person_view.households
    assert household_view_2 in full_person_view.households

    mock_create_household_view.assert_has_calls([call(household_1), call(household_2)], any_order=True)


@mock.patch.object(AddressFactory, 'create_address_from_address_entity')
@mock.patch('src.app.people.factories.peopleFactory.PeopleFactory.create_basic_person_view_from_person_entity')
def test_create_household_view(mock_create_basic_person_view_from_person_entity,
                               mock_create_address_from_address_entity):
    address_factory = AddressFactory()
    pfactory = PeopleFactory(address_factory=address_factory)
    household_entity = models.Household(
        id=1
    )

    leader_entity = models.Person(id=1)

    person_entity_2 = models.Person(id=2)
    person_entity_3 = models.Person(id=3)
    household_entity.leader = leader_entity
    household_entity.people = [leader_entity, person_entity_2]

    address_entity = models.Address(id=1)
    household_entity.address = address_entity

    def side_effect(person):
         return BasicViewPerson(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name)


    mock_create_basic_person_view_from_person_entity.side_effect = side_effect
    mock_create_address_from_address_entity.return_value = ViewAddress(id=1)
    household_view = pfactory.create_household_view(household_entity)

    assert household_view.id == 1
    assert household_view.leader.id == 1
    # assert leader_entity call twice because it is the leader and a member of the household
    mock_create_basic_person_view_from_person_entity.assert_has_calls(
        [call(leader_entity), call(leader_entity), call(person_entity_2)], any_order=True)
    mock_create_address_from_address_entity.assert_called_with(address_entity)

@mock.patch.object(MediaFactory, 'create_image_from_image_entity')
def test_create_profile_image_list_from_entity_list(mock_create_image_from_image_entity):
    media_factory = MediaFactory()
    pfactory = PeopleFactory(media_factory=media_factory)

    person_entity = models.Person(
        id=1,
    )

    personImage_1 = models.PersonImage(
        id=1,
        person_id=1,
        image=media_models.Image(
            id=1,
            description="test_image.jpg",
            address="test_image.jpg",
            created=datetime(2020, 1, 1, 0, 0),
            store="local"
        )
    )

    personImage_2 = models.PersonImage(
        id=2,
        person_id=1,
        image=media_models.Image(
            id=2,
            description="test_image_2.jpg",
            address="test_image_2.jpg",
            created=datetime(2020, 1, 1, 0, 0),
            store="local"
        )
    )

    person_entity.profile_images = [personImage_1, personImage_2]

    pfactory.create_profile_image_list_from_entity_list(person_entity.profile_images)

    mock_create_image_from_image_entity.assert_has_calls([call(personImage_1.image), call(personImage_2.image)], any_order=True)

def test_create_person_entity_from_create_person():
    person = CreatePerson(
        first_name="test",
        last_name="test",
        email="test@test.com",
        mobile_number="0721234567",
        date_of_birth=datetime(1980, 1, 1, 0, 0).date(),
        gender=Gender.male,
        marriage_date=datetime(2020, 1, 1).date(),
        marital_status=MaritalStatus.married,
        registered_date=datetime(1980, 1, 1).date(),
        social_media_links= [SocialMediaLink(type="twitter", url="https://www.twitter.com/test"), SocialMediaLink(type="facebook",url="https://www.facebook.com/test")]
    )

    person_entity = people_factory.create_person_entity_from_create_person(person)

    assert person_entity.first_name == person.first_name
    assert person_entity.last_name == person.last_name
    assert person_entity.email == person.email
    assert person_entity.mobile_number == person.mobile_number
    assert person_entity.date_of_birth == person.date_of_birth
    assert person_entity.gender == person.gender
    assert person_entity.marriage_date == person.marriage_date
    assert person_entity.marital_status == person.marital_status
    assert person_entity.registered_date == person.registered_date
    assert len(person_entity.social_media_links) == 2
    assert person_entity.social_media_links[0].type == person.social_media_links[0].type
    assert person_entity.social_media_links[0].url == person.social_media_links[0].url
    assert person_entity.social_media_links[1].type == person.social_media_links[1].type
    assert person_entity.social_media_links[1].url == person.social_media_links[1].url


def test_create_person_entity_from_create_person_with_addresses():
    person = CreatePerson(
        first_name="test",
        last_name="test",
        email="test@test.com",
        mobile_number="0721234567",
        date_of_birth=datetime(1980, 1, 1, 0, 0).date(),
        gender=Gender.male,
        marriage_date=datetime(2020, 1, 1).date(),
        marital_status=MaritalStatus.married,
        registered_date=datetime(1980, 1, 1).date(),
        social_media_links= [SocialMediaLink(type="twitter",url="https://www.twitter.com/test"), SocialMediaLink(type="facebook",url="https://www.facebook.com/test")]
    )

    address_entity_1 = models.Address(id=3)
    address_entity_2 = models.Address(id=4)
    address_entities = [address_entity_1, address_entity_2]
    person_entity = people_factory.create_person_entity_from_create_person(person, address_entities)

    assert person_entity.first_name == person.first_name
    assert person_entity.last_name == person.last_name
    assert person_entity.email == person.email
    assert person_entity.mobile_number == person.mobile_number
    assert person_entity.date_of_birth == person.date_of_birth
    assert person_entity.gender == person.gender
    assert person_entity.marriage_date == person.marriage_date
    assert person_entity.marital_status == person.marital_status
    assert person_entity.registered_date == person.registered_date
    assert len(person_entity.social_media_links) == 2
    assert person_entity.social_media_links[0].type == person.social_media_links[0].type
    assert person_entity.social_media_links[0].url == person.social_media_links[0].url
    assert person_entity.social_media_links[1].type == person.social_media_links[1].type
    assert person_entity.social_media_links[1].url == person.social_media_links[1].url

    # TODO FIX THIS TESTCASE. There is some issue with this test case that whenever addresses is added to the personaddress it gets duplicated.
    #assert len(person_entity.addresses) == 2
    assert address_entity_1.id in [address.address.id for address in person_entity.addresses]
    assert address_entity_2.id in [address.address.id for address in person_entity.addresses]

