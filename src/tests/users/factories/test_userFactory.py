from unittest import mock

from src.app.people.models.database.models import Person
from src.app.users.factories.userFactory import UserFactory
from src.app.users.models.database import models
from src.app.users.models.user import User
from src.app.users.services.passwordUtil import PasswordUtil


def test_create_user_from_user_entity():
    factory = UserFactory(password_utils=PasswordUtil())
    entity = models.User(
        id=1,
        first_name="Joe",
        last_name="Soap",
        email="joe@test.com",
        mobile_number="+271234",
        password="hashed",
        person_id=5,
    )

    user = factory.create_user_from_user_entity(entity)

    assert user.id == 1
    assert user.email == "joe@test.com"
    assert user.password == "hashed"
    assert user.person_id == 5


def test_create_display_user_from_user_entity():
    factory = UserFactory(password_utils=PasswordUtil())
    entity = models.User(
        id=1,
        first_name="Joe",
        last_name="Soap",
        email="joe@test.com",
        mobile_number="+271234",
        password="hashed",
        person_id=5,
    )

    display = factory.create_display_user_from_user_entity(entity)

    assert display.id == 1
    assert display.email == "joe@test.com"
    assert display.first_name == "Joe"
    assert not hasattr(display, "password") or "password" not in display.model_dump()


@mock.patch.object(PasswordUtil, "hash_pwd")
def test_create_user_entity_from_user_hashes_password(mock_hash_pwd):
    mock_hash_pwd.return_value = "hashed-password"
    factory = UserFactory(password_utils=PasswordUtil())
    user = User(
        first_name="Joe",
        last_name="Soap",
        email="joe@test.com",
        mobile_number="+271234",
        password="plain",
    )

    entity = factory.create_user_entity_from_user(user)

    assert entity.password == "hashed-password"
    assert entity.email == "joe@test.com"
    mock_hash_pwd.assert_called_once_with("plain")


@mock.patch.object(PasswordUtil, "hash_pwd")
def test_create_user_entity_from_person(mock_hash_pwd):
    mock_hash_pwd.return_value = "derived-hash"
    factory = UserFactory(password_utils=PasswordUtil())
    person = Person(
        id=9,
        first_name="Ann",
        last_name="Lee",
        email="ann@test.com",
        mobile_number="+27999",
    )

    entity = factory.create_user_entity_from_person(person)

    assert entity.person_id == 9
    assert entity.email == "ann@test.com"
    assert entity.password == "derived-hash"
    mock_hash_pwd.assert_called_once_with("AnnLee")
