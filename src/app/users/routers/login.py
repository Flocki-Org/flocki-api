from fastapi import APIRouter, Depends, status, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from src.app.config import settings

from src.app.users.models.login import AuthResponse
from ..services.authService import AuthService, InvalidAuthCredentials, InvalidPasswordException, NoUserException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(tags=['Login'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl ="login")

@router.post('/login', response_model=AuthResponse)
def login(request: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(AuthService)):
    try:
        return auth_service.login_basic_auth(request.username, request.password, True)
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
        # get client id from config client_id
        client_id = settings.flocki_google_client_id
        token_uri = "https://oauth2.googleapis.com/token"
        request = requests.Request()

        access_token_info = id_token.verify_oauth2_token(
            token, request)

        print(access_token_info['aud'])
        # Check if the token is valid for your app and was issued to the correct client ID
        if access_token_info['aud'] != client_id:
            raise ValueError('Token was not issued for this client ID')

        if access_token_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise HTTPException(status_code=401, detail='Invalid issuer')

        print("Verified Google token: ${token}")
        # If the token is valid, return the user's email address
        return auth_service.login(access_token_info['email'])
    except ValueError as e:
        # If the token is invalid, return a 401 Unauthorized error
        print(e)
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


def get_current_user(token: AuthResponse = Depends(oauth2_scheme), auth_service: AuthService = Depends(AuthService)):
    try:
        if isinstance(token, str):
            return auth_service.get_current_user(token)

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})
    except InvalidAuthCredentials as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth credentials",
                      headers={'WWW-Authenticate': "Bearer"})