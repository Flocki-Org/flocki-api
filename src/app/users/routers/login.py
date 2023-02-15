from fastapi import APIRouter, Depends, status, HTTPException
from src.app.database import get_db, SessionLocal
from src.app.users.models.database import models
from src.app.users.models.login import Token, TokenData
from sqlalchemy import func

from ..daos.userDAO import UserDAO
from src.app.users.models.login import AuthResponse
from ..services.authService import AuthService, InvalidAuthCredentials, InvalidPasswordException, NoUserException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(tags=['Login'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl ="login")

@router.post('/login', response_model=AuthResponse)
def login(request: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(AuthService)):
    try:
        return auth_service.login(request.username, request.password)
    except InvalidPasswordException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid username or password",
                      headers={'WWW-Authenticate': "Bearer"})
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid username or password",
                            headers={'WWW-Authenticate': "Bearer"})

def get_current_user(token: AuthResponse = Depends(oauth2_scheme), auth_service: AuthService = Depends(AuthService)):
    try:
        if isinstance(token, str):
            return auth_service.get_current_user(token)

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})
    except InvalidAuthCredentials as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})