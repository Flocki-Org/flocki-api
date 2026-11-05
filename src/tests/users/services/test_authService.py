from unittest import mock

import pytest

from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import BasicViewPerson
from src.app.users.daos.userDAO import UserDAO
from src.app.users.factories.userFactory import UserFactory
from src.app.users.models.database import models
from src.app.users.models.user import DisplayUser
from src.app.users.services.TokenUtil import TokenUtil
from src.app.users.services.authService import (
    AuthService,
    InvalidAuthCredentials,
    InvalidPasswordException,
    NoUserException,
)
from src.app.users.services.passwordUtil import PasswordUtil


def _build_service():
    return AuthService(
        user_DAO=UserDAO(),
        token_util=TokenUtil(),
        password_utils=PasswordUtil(),
        user_factory=UserFactory(),
        person_DAO=PeopleDAO(),
        people_factory=PeopleFactory(),
    )


@mock.patch.object(PeopleFactory, "create_basic_person_view_from_person_entity")
@mock.patch.object(UserFactory, "create_display_user_from_user_entity")
@mock.patch.object(PeopleDAO, "get_person_by_id")
@mock.patch.object(TokenUtil, "generate_token")
@mock.patch.object(PasswordUtil, "verify_pwd")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_basic_auth_success(
    mock_get_user_by_name,
    mock_verify_pwd,
    mock_generate_token,
    mock_get_person_by_id,
    mock_create_display_user,
    mock_create_basic_person,
):
    auth_service = _build_service()
    user = models.User(id=1, email="joe@test.com", password="hashed", person_id=10)
    mock_get_user_by_name.return_value = user
    mock_verify_pwd.return_value = True
    mock_generate_token.return_value = "jwt-token"
    mock_get_person_by_id.return_value = mock.Mock(id=10)
    display_user = DisplayUser(id=1, first_name="Joe", last_name="Soap", email="joe@test.com")
    mock_create_display_user.return_value = display_user
    basic_person = BasicViewPerson(id=10, first_name="Joe", last_name="Soap")
    mock_create_basic_person.return_value = basic_person

    response = auth_service.login_basic_auth("joe@test.com", "password")

    assert response.access_token == "jwt-token"
    assert response.token_type == "bearer"
    assert response.user == display_user
    assert response.person == basic_person
    mock_generate_token.assert_called_once_with(data={"sub": "joe@test.com"})


@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_basic_auth_unknown_user(mock_get_user_by_name):
    auth_service = _build_service()
    mock_get_user_by_name.return_value = None

    with pytest.raises(NoUserException):
        auth_service.login_basic_auth("missing@test.com", "password")


@mock.patch.object(PasswordUtil, "verify_pwd")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_basic_auth_invalid_password(mock_get_user_by_name, mock_verify_pwd):
    auth_service = _build_service()
    mock_get_user_by_name.return_value = models.User(id=1, email="joe@test.com", password="hashed")
    mock_verify_pwd.return_value = False

    with pytest.raises(InvalidPasswordException):
        auth_service.login_basic_auth("joe@test.com", "wrong")


@mock.patch.object(PasswordUtil, "verify_pwd")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_basic_auth_can_skip_password_validation(mock_get_user_by_name, mock_verify_pwd):
    auth_service = _build_service()
    user = models.User(id=1, email="joe@test.com", password="hashed", person_id=None)
    mock_get_user_by_name.return_value = user

    with mock.patch.object(TokenUtil, "generate_token", return_value="token"), \
            mock.patch.object(PeopleDAO, "get_person_by_id", return_value=None), \
            mock.patch.object(UserFactory, "create_display_user_from_user_entity",
                              return_value=DisplayUser(id=1, first_name="Joe", last_name="Soap", email="joe@test.com")):
        response = auth_service.login_basic_auth("joe@test.com", "ignored", validate_password=False)

    assert response.access_token == "token"
    mock_verify_pwd.assert_not_called()


@mock.patch.object(UserFactory, "create_display_user_from_user_entity")
@mock.patch.object(PeopleDAO, "get_person_by_id")
@mock.patch.object(TokenUtil, "generate_token")
@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_without_linked_person(
    mock_get_user_by_name,
    mock_generate_token,
    mock_get_person_by_id,
    mock_create_display_user,
):
    auth_service = _build_service()
    user = models.User(id=1, email="joe@test.com", password="hashed", person_id=None)
    mock_get_user_by_name.return_value = user
    mock_generate_token.return_value = "google-jwt"
    mock_get_person_by_id.return_value = None
    mock_create_display_user.return_value = DisplayUser(
        id=1, first_name="Joe", last_name="Soap", email="joe@test.com"
    )

    response = auth_service.login("joe@test.com")

    assert response.access_token == "google-jwt"
    assert response.person is None


@mock.patch.object(UserDAO, "get_user_by_name")
def test_login_unknown_user(mock_get_user_by_name):
    auth_service = _build_service()
    mock_get_user_by_name.return_value = None

    with pytest.raises(NoUserException):
        auth_service.login("missing@test.com")


@mock.patch.object(TokenUtil, "decode_token")
def test_get_current_user_success(mock_decode_token):
    auth_service = _build_service()
    mock_decode_token.return_value = {"sub": "joe@test.com"}

    token_data = auth_service.get_current_user("valid-token")

    assert token_data.username == "joe@test.com"


@mock.patch.object(TokenUtil, "decode_token")
def test_get_current_user_missing_subject(mock_decode_token):
    auth_service = _build_service()
    mock_decode_token.return_value = {}

    with pytest.raises(InvalidAuthCredentials):
        auth_service.get_current_user("token")


@mock.patch.object(TokenUtil, "decode_token")
def test_get_current_user_invalid_token(mock_decode_token):
    auth_service = _build_service()
    mock_decode_token.side_effect = Exception("bad token")

    with pytest.raises(InvalidAuthCredentials):
        auth_service.get_current_user("token")
