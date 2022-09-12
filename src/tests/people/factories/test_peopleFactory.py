
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, Mock

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.media import CreateImage, ViewImage
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.database import models
from src.app.people.models.people import SocialMediaLink
from src.app.media.models.database import models as media_models

#Mock.patch("src.app.media.factories.mediaFactory.MediaFactory")

people_factory = PeopleFactory()

def test_create_basic_person_view_from_person_entity():
    # we create a new entity in each test to keep them independent
    person_entity = models.Person(
        id = 1,
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

@mock.patch.object(MediaFactory, 'createViewImageFromImageEntity')
def test_create_person_from_person_entity(mock_createViewImageFromImageEntity):
    media_factory = MediaFactory()
    pfactory = PeopleFactory(media_factory=media_factory)

    person_entity = models.Person(
        id=1,
        first_name="Test Name",
        last_name="Last Name",
        email="test@test.com",
        mobile_number="0721231234",
        gender="male",
        marital_status="single",
    )
    sml_fb: SocialMediaLink = models.SocialMediaLink(
        person_id=person_entity.id,
        type="facebook",
        url="https://www.facebook.com/test")

    sml_twitter: SocialMediaLink = models.SocialMediaLink(
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
    personImageEntity_1 = models.PersonImage(id=1, person_id=person_entity.id, image=image_entity_1)
    personImageEntity_2 = models.PersonImage(id=2, person_id=person_entity.id, image=image_entity_2)
    person_entity.profile_images = [personImageEntity_1, personImageEntity_2]

    full_person_view = pfactory.create_person_from_person_entity(person_entity, include_households=False, include_profile_image=True)

    assert full_person_view.id == 1
    assert full_person_view.first_name == person_entity.first_name
    assert full_person_view.last_name == person_entity.last_name
    assert full_person_view.email == person_entity.email
    assert full_person_view.mobile_number == person_entity.mobile_number
    assert full_person_view.gender == "male"
    assert full_person_view.marital_status == "single"

    mock_createViewImageFromImageEntity.assert_called_with(image_entity_2)
    media_factory.createViewImageFromImageEntity.assert_called_with(image_entity_2)
    #assert full_person_view.profile_image.id == image_entity_1.description
    #assert full_person_view.profile_image.description == image_entity_1.description