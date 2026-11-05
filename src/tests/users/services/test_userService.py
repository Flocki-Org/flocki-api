from unittest import mock

import pytest
from fastapi_pagination import Page, Params

from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.models.database import models as people_models
from src.app.users.daos.userDAO import UserDAO
from src.app.users.factories.userFactory import UserFactory
from src.app.users.models.database import models
from src.app.users.models.user import DisplayUser, User
from src.app.users.services.passwordUtil import PasswordUtil
from src.app.users.services.userService import (
    AlreadyExistPersonAssociatedWithUser,
    ExistingUserExistsException,
    NoPersonException,
    NoUserException,
    UserService,
)


def _build_service():
    return UserService(
        user_factory=UserFactory(password_utils=PasswordUtil()),
        user_DAO=UserDAO(),
        password_utils=PasswordUtil(),
        peopleDAO=PeopleDAO(),
    )


@mock.patch.object(UserFactory, "create_user_from_user_entity")
@mock.patch.object(UserDAO, "get_all_users")
def test_get_all_users(mock_get_all_users, mock_create_user):
    service = _build_service()
    entity_1 = models.User(id=1, email="a@test.com")
    entity_2 = models.User(id=2, email="b@test.com")
    mock_get_all_users.return_value = Page.create(
        items=[entity_1, entity_2], total=2, params=Params(page=1, size=10)
    )
    user_1 = User(id=1, first_name="A", last_name="A", email="a@test.com", mobile_number="1", password="x")
    user_2 = User(id=2, first_name="B", last_name="B", email="b@test.com", mobile_number="2", password="x")
    mock_create_user.side_effect = [user_1, user_2]

    page = service.get_all_users(Params(page=1, size=10))

    assert page.items == [user_1, user_2]
    assert page.total == 2


@mock.patch.object(UserDAO, "get_all_users")
def test_get_all_users_empty(mock_get_all_users):
    service = _build_service()
    mock_get_all_users.return_value = None

    assert service.get_all_users() == []


@mock.patch.object(UserFactory, "create_user_from_user_entity")
@mock.patch.object(UserDAO, "get_user_by_id")
def test_get_user_by_id(mock_get_user_by_id, mock_create_user):
    service = _build_service()
    entity = models.User(id=1, email="a@test.com")
    mock_get_user_by_id.return_value = entity
    expected = User(id=1, first_name="A", last_name="A", email="a@test.com", mobile_number="1", password="x")
    mock_create_user.return_value = expected

    assert service.get_user_by_id(1) == expected


@mock.patch.object(UserDAO, "get_user_by_id")
def test_get_user_by_id_missing(mock_get_user_by_id):
    service = _build_service()
    mock_get_user_by_id.return_value = None

    with pytest.raises(NoUserException):
        service.get_user_by_id(99)


@mock.patch.object(UserDAO, "get_user_by_name")
def test_get_user_by_name_delegates_to_dao(mock_get_user_by_name):
    service = _build_service()
    mock_get_user_by_name.return_value = models.User(id=1, email="a@test.com")

    result = service.get_user_by_name("a@test.com")

    assert result.email == "a@test.com"
    mock_get_user_by_name.assert_called_once_with("a@test.com")


@mock.patch.object(UserFactory, "create_user_from_user_entity")
@mock.patch.object(UserDAO, "create_user")
@mock.patch.object(UserFactory, "create_user_entity_from_user")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_create_user_success(
    mock_get_user_by_name, mock_create_entity, mock_create_user, mock_create_user_model
):
    service = _build_service()
    new_user = User(first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="secret")
    mock_get_user_by_name.return_value = None
    entity = models.User(id=1, email="a@test.com")
    mock_create_entity.return_value = entity
    mock_create_user.return_value = entity
    expected = User(id=1, first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="hashed")
    mock_create_user_model.return_value = expected

    result = service.create_user(new_user)

    assert result == expected
    mock_create_user.assert_called_once_with(entity)


@mock.patch.object(UserDAO, "get_user_by_name")
def test_create_user_duplicate_email(mock_get_user_by_name):
    service = _build_service()
    mock_get_user_by_name.return_value = models.User(id=1, email="a@test.com")

    with pytest.raises(ExistingUserExistsException):
        service.create_user(
            User(first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="secret")
        )


@mock.patch.object(UserFactory, "create_display_user_from_user_entity")
@mock.patch.object(UserDAO, "create_user")
@mock.patch.object(UserFactory, "create_user_entity_from_person")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_create_user_from_person(
    mock_get_user_by_name, mock_create_entity, mock_create_user, mock_create_display
):
    service = _build_service()
    person = people_models.Person(id=5, first_name="Ann", last_name="Lee", email="ann@test.com", mobile_number="1")
    mock_get_user_by_name.return_value = None
    entity = models.User(id=2, email="ann@test.com", person_id=5)
    mock_create_entity.return_value = entity
    mock_create_user.return_value = entity
    display = DisplayUser(id=2, first_name="Ann", last_name="Lee", email="ann@test.com")
    mock_create_display.return_value = display

    result = service.create_user_from_person(person)

    assert result == display


@mock.patch.object(UserDAO, "get_user_by_name")
def test_create_user_from_person_duplicate(mock_get_user_by_name):
    service = _build_service()
    mock_get_user_by_name.return_value = models.User(id=1, email="ann@test.com")

    with pytest.raises(ExistingUserExistsException):
        service.create_user_from_person(
            people_models.Person(id=5, first_name="Ann", last_name="Lee", email="ann@test.com")
        )


@mock.patch.object(UserService, "get_user_by_id")
@mock.patch.object(UserDAO, "update_user")
@mock.patch.object(PasswordUtil, "hash_pwd")
@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_hashes_password(
    mock_get_user_by_id, mock_hash_pwd, mock_update_user, mock_service_get_user
):
    service = _build_service()
    mock_get_user_by_id.return_value = models.User(id=1, email="a@test.com")
    mock_hash_pwd.return_value = "hashed-secret"
    updated = User(id=1, first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="hashed-secret")
    mock_service_get_user.return_value = updated
    update_payload = User(first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="plain")

    result = service.update_user(1, update_payload)

    assert result == updated
    update_values = mock_update_user.call_args[0][1]
    assert update_values["password"] == "hashed-secret"


@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_missing(mock_get_user_by_id):
    service = _build_service()
    mock_get_user_by_id.return_value = None

    with pytest.raises(NoUserException):
        service.update_user(
            1, User(first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="x")
        )


@mock.patch.object(UserFactory, "create_user_from_user_entity")
@mock.patch.object(UserDAO, "update_user_person")
@mock.patch.object(PeopleDAO, "get_person_by_id")
@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_person_success(
    mock_get_user_by_id, mock_get_person_by_id, mock_update_user_person, mock_create_user
):
    service = _build_service()
    mock_get_user_by_id.side_effect = [
        models.User(id=1, email="a@test.com"),
        models.User(id=1, email="a@test.com", person_id=9),
    ]
    person = people_models.Person(id=9, first_name="P", last_name="Q")
    person.user = None
    mock_get_person_by_id.return_value = person
    expected = User(id=1, first_name="A", last_name="B", email="a@test.com", mobile_number="1", password="x", person_id=9)
    mock_create_user.return_value = expected

    result = service.update_user_person(1, 9)

    assert result == expected
    mock_update_user_person.assert_called_once_with(1, 9)


@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_person_missing_user(mock_get_user_by_id):
    service = _build_service()
    mock_get_user_by_id.return_value = None

    with pytest.raises(NoUserException):
        service.update_user_person(1, 9)


@mock.patch.object(PeopleDAO, "get_person_by_id")
@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_person_missing_person(mock_get_user_by_id, mock_get_person_by_id):
    service = _build_service()
    mock_get_user_by_id.return_value = models.User(id=1, email="a@test.com")
    mock_get_person_by_id.return_value = None

    with pytest.raises(NoPersonException):
        service.update_user_person(1, 9)


@mock.patch.object(PeopleDAO, "get_person_by_id")
@mock.patch.object(UserDAO, "get_user_by_id")
def test_update_user_person_already_associated(mock_get_user_by_id, mock_get_person_by_id):
    service = _build_service()
    mock_get_user_by_id.return_value = models.User(id=1, email="a@test.com")
    person = people_models.Person(id=9, first_name="P", last_name="Q")
    person.user = models.User(id=2, email="other@test.com")
    mock_get_person_by_id.return_value = person

    with pytest.raises(AlreadyExistPersonAssociatedWithUser):
        service.update_user_person(1, 9)
