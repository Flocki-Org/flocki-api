from fastapi import Depends

from src.app.users.daos.userDAO import UserDAO
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
    def __init__(self, user_DAO: UserDAO = Depends(UserDAO), token_util: TokenUtil = Depends(TokenUtil), password_utils: PasswordUtil = Depends(PasswordUtil)):
        self.password_utils = password_utils
        self.user_DAO = user_DAO
        self.token_util = token_util

    def login(self, username, password):
        user = self.user_DAO.get_user_by_name(username)
        if user is None:
            raise NoUserException("Invalid user name")

        if not self.password_utils.verify_pwd(password, user.password):
            raise InvalidPasswordException("Invalid password")

        access_token = self.token_util.generate_token(
            data={"sub": user.email}
        )

        return {"access_token": access_token, "token_type": "bearer"}

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