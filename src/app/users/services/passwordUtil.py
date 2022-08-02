from passlib.context import CryptContext

ALGORITHM = "HS256"

class PasswordUtil:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        pass

    def hash_pwd(self,pwd):
        return self.pwd_context.hash(pwd)

    def verify_pwd(self, pwd, db_pwd_hash):
        return self.pwd_context.verify(pwd, db_pwd_hash)
