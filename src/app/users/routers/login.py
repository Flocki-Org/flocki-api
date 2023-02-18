from fastapi import APIRouter, Depends, status, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests

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

@router.post("/login_with_google_token", response_model=AuthResponse)
async def verify_google_token(token: str, auth_service: AuthService = Depends(AuthService)):
    try:
        print("Attempting to verify Google token: ${token}")
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise HTTPException(status_code=401, detail='Invalid issuer')

        print("Verified Google token: ${token}")
        # If the token is valid, return the user's email address
        return auth_service.login(idinfo['email'])
    except ValueError as e:
        # If the token is invalid, return a 401 Unauthorized error
        raise HTTPException(status_code=401, detail=str(e))


def get_current_user(token: AuthResponse = Depends(oauth2_scheme), auth_service: AuthService = Depends(AuthService)):
    try:
        if isinstance(token, str):
            return auth_service.get_current_user(token)

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})
    except InvalidAuthCredentials as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})