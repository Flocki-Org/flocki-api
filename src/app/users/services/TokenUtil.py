from datetime import datetime, timedelta
from src.app.config import settings
from jose import jwt, JWTError

ALGORITHM = "HS256"

def generate_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes = settings.token_expiry_minutes)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])