from fastapi import Depends

from src.app.users.models.user import User
from src.app.users.models.database import models

from src.app.users.services.passwordUtil import PasswordUtil

class UserFactory:
    def __init__(self, password_utils: PasswordUtil = Depends(PasswordUtil)):
        self.password_utils = password_utils
        pass

    def createUserFromUserEntity(self, user_entity):
        user_response = User(
            id=user_entity.id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            mobile_number=user_entity.mobile_number,
            password=user_entity.password
        )
        return user_response

    def createUserEntityFromUser(self, user):
        password_hashed = self.password_utils.hash_pwd(user.password)
        new_user = models.User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            mobile_number=user.mobile_number,
            password=password_hashed,
        )
        return new_user
