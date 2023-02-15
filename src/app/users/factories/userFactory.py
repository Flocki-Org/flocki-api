from fastapi import Depends

from src.app.people.models.database.models import Person
from src.app.users.models.user import User, DisplayUser
from src.app.users.models.database import models

from src.app.users.services.passwordUtil import PasswordUtil

class UserFactory:
    def __init__(self, password_utils: PasswordUtil = Depends(PasswordUtil)):
        self.password_utils = password_utils
        pass

    def create_user_from_user_entity(self, user_entity: models.User) -> User:
        user_response = User(
            id=user_entity.id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            mobile_number=user_entity.mobile_number,
            password=user_entity.password,
            person_id=user_entity.person_id
        )
        return user_response

    def create_display_user_from_user_entity(self, user_entity: models.User) -> User:
        user_response = DisplayUser(
            id=user_entity.id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            mobile_number=user_entity.mobile_number,
            password=user_entity.password,
            person=user_entity.person
        )
        return user_response

    def create_user_entity_from_user(self, user):
        password_hashed = self.password_utils.hash_pwd(user.password)
        new_user = models.User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            mobile_number=user.mobile_number,
            password=password_hashed,
        )
        return new_user

    def create_user_entity_from_person(self, person: Person) -> models.User:
        new_user = models.User(
            first_name=person.first_name,
            last_name=person.last_name,
            email=person.email,
            mobile_number=person.mobile_number,
            password=self.password_utils.hash_pwd(person.first_name + person.last_name),
            person_id=person.id
        )
        return new_user

