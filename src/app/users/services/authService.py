from fastapi import Depends

from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.users.daos.userDAO import UserDAO
from src.app.users.factories.userFactory import UserFactory
from src.app.users.models.login import AuthResponse, Token
from src.app.users.models.login import TokenData
from src.app.users.services.TokenUtil import TokenUtil
from src.app.users.services.passwordUtil import PasswordUtil


class NoUserException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class InvalidAuthCredentials(Exception):
    pass

class AuthService:
    def __init__(self, user_DAO: UserDAO = Depends(UserDAO), token_util: TokenUtil = Depends(TokenUtil), password_utils: PasswordUtil = Depends(PasswordUtil),
                 user_factory: UserFactory = Depends(UserFactory), person_DAO: PeopleDAO = Depends(PeopleDAO), people_factory: PeopleFactory = Depends(PeopleFactory)):
        self.password_utils = password_utils
        self.user_DAO = user_DAO
        self.token_util = token_util
        self.user_factory = user_factory
        self.person_DAO = person_DAO
        self.people_factory = people_factory

    def login_basic_auth(self, username, password, validate_password=True) -> AuthResponse:
        user = self.user_DAO.get_user_by_name(username)
        if user is None:
            raise NoUserException("Invalid user name")

        if validate_password and not self.password_utils.verify_pwd(password, user.password):
            raise InvalidPasswordException("Invalid password")

        access_token = self.token_util.generate_token(
            data={"sub": user.email}
        )

        linked_person = self.person_DAO.get_person_by_id(user.person_id)
        basic_view_person = None
        if linked_person is not None:
            basic_view_person = self.people_factory.create_basic_person_view_from_person_entity(linked_person)

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=self.user_factory.create_display_user_from_user_entity(user),
            person=basic_view_person
        )

    def login(self, username) -> AuthResponse:
        # this gets user by name or email address
        user = self.user_DAO.get_user_by_name(username)
        if user is None:
            raise NoUserException("Invalid user name")

        access_token = self.token_util.generate_token(
            data={"sub": user.email}
        )

        linked_person = self.person_DAO.get_person_by_id(user.person_id)
        basic_view_person = None
        if linked_person is not None:
            basic_view_person = self.people_factory.create_basic_person_view_from_person_entity(linked_person)

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=self.user_factory.create_display_user_from_user_entity(user),
            person=basic_view_person
        )

    def get_current_user(self, token):
        invalid_auth_exception = InvalidAuthCredentials("Invalid Auth")
        try:
            decoded_token = self.token_util.decode_token(token)
            user_name: str = decoded_token.get('sub')
            if user_name is None:
                raise invalid_auth_exception
            return TokenData(username=user_name)
        except:
            raise invalid_auth_exception

