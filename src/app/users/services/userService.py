from fastapi import Depends

from src.app.users.daos.userDAO import UserDAO
from src.app.users.factories.userFactory import UserFactory
from src.app.users.services.passwordUtil import PasswordUtil


class NoUserException(Exception):
    pass

class UserService:
    def __init__(self, user_factory: UserFactory = Depends(UserFactory), user_DAO: UserDAO = Depends(UserDAO), password_utils: PasswordUtil = Depends(PasswordUtil)):
        self.user_factory = user_factory
        self.user_DAO = user_DAO
        self.password_utils = password_utils

    def get_all_users(self):
        user_entities = self.user_DAO.get_all_users()
        for user_entity in user_entities:
            yield self.user_factory.create_user_from_user_entity(user_entity)

    def get_user_by_id(self, id):
        user_entity = self.user_DAO.get_user_by_id(id)
        if user_entity is None:
            raise NoUserException("User with that id does not exist")
        return self.user_factory.create_user_from_user_entity(user_entity)

    def get_user_by_name(self, name):
        return self.user_DAO.get_user_by_name(name)

    def create_user(self, new_user):
        new_user_entity = self.user_factory.create_user_entity_from_user(new_user)
        response_new_user_entity = self.user_DAO.create_user(new_user_entity)
        return self.user_factory.create_user_from_user_entity(response_new_user_entity)

    def update_user(self, user_id, update_user):
        userToUpdate = self.user_DAO.get_user_by_id(user_id)
        if userToUpdate is None:
            raise NoUserException("User with that id does not exist")
        # For update requests the model is not expected to come in with an ID since it is passed in the URL.
        update_values = update_user.dict()
        if 'password' in update_values:
            update_values['password'] = self.password_utils.hash_pwd(update_values['password'])

        self.user_DAO.update_user(user_id, update_values)
        return self.get_user_by_id(user_id)