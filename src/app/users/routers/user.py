from fastapi import status, Depends, HTTPException

from .login import get_current_user
from ..services.userService import UserService, NoUserException
from ...users.models.user import User, DisplayUser
from fastapi import APIRouter
from typing import List

router = APIRouter(tags=['Users'])

@router.get('/users', response_model=List[DisplayUser])
def get_users(user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    return user_service.get_all_users()

@router.get('/user/{id}', response_model=DisplayUser)
def get_user(id: int, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.get_user_by_id(id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that id does not exist")
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)

@router.put('/user/')
def update_user(id:int, user: User, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.update_user(id, user)
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)

@router.post('/user', status_code = status.HTTP_201_CREATED, response_model=DisplayUser)
def add_user(user: User, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    return user_service.create_user(user)

