import bcrypt

ALGORITHM = "HS256"

class PasswordUtil:
    def __init__(self):
        pass

    def hash_pwd(self, pwd):
        if isinstance(pwd, str):
            pwd = pwd.encode("utf-8")
        return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")

    def verify_pwd(self, pwd, db_pwd_hash):
        if isinstance(pwd, str):
            pwd = pwd.encode("utf-8")
        if isinstance(db_pwd_hash, str):
            db_pwd_hash = db_pwd_hash.encode("utf-8")
        return bcrypt.checkpw(pwd, db_pwd_hash)
