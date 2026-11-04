from datetime import UTC, datetime, timedelta
from src.app.config import settings
import jwt

ALGORITHM = "HS256"

class TokenUtil:
    def __init__(self):
        pass

    def generate_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(minutes = settings.flocki_token_expiry_minutes)
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode, settings.flocki_secret_key, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str):
        return jwt.decode(token, settings.flocki_secret_key, algorithms=[ALGORITHM])
