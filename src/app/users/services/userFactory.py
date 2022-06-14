from ...users.models.user import User
from ...users.models.database import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def createUserFromUserEntity(user_entity):
    user_response = User(
        id=user_entity.id,
        first_name=user_entity.first_name,
        last_name=user_entity.last_name,
        email=user_entity.email,
        mobile_number=user_entity.mobile_number,
        password=user_entity.password
    )
    return user_response


def createUserEntityFromUser(user):
    password_hashed = hash_pwd(user.password)
    new_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=user.mobile_number,
        password=password_hashed,
    )
    return new_user


def hash_pwd(pwd):
    return pwd_context.hash(pwd)

def verify_pwd(pwd, db_pwd_hash):
    return pwd_context.verify(pwd, db_pwd_hash)