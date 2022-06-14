from fastapi import Depends
from fastapi import APIRouter, Depends, status, HTTPException
from src.app.database import get_db, SessionLocal
from src.app.users.models.database import models
from src.app.users.models.login import Token, TokenData
from ...users.services.userFactory import verify_pwd
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...users.services.TokenUtil import generate_token, decode_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl ="login")

@router.post('/login', response_model=Token)
def login(request: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(func.lower(models.User.email) == func.lower(request.username.upper())).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='username or password invalid')

    if not verify_pwd(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='username or password invalid')

    access_token = generate_token(
        data={"sub": user.email}
    )

    return {"access_token":access_token,"token_type":"bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    invalid_auth_exception = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials", headers={'WWW-Authenticate': "Bearer"})
    try:
        decoded_token = decode_token(token)
        user_name: str = decoded_token.get('sub')
        if user_name is None:
            raise invalid_auth_exception
        return TokenData(username = user_name)
    except:
        raise invalid_auth_exception