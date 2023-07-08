from fastapi import status, Depends, HTTPException

from fastapi_pagination import Page, Params

from .login import get_current_user
from ..services.userService import UserService, NoUserException, ExistingUserExistsException, \
    AlreadyExistPersonAssociatedWithUser
from ...users.models.user import User, DisplayUser
from fastapi import APIRouter
from typing import List

router = APIRouter(tags=['Users'])

@router.get('/users', response_model=Page[DisplayUser])
def get_users(page: int = 1, page_size: int = 100, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    return user_service.get_all_users(Params(page=page, size=page_size))

@router.get('/users/{id}', response_model=User)
def get_user(id: int, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.get_user_by_id(id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that id does not exist")
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that id does not exist")

@router.put('/users/')
def update_user(id:int, user: User, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.update_user(id, user)
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])

@router.post('/users', status_code = status.HTTP_201_CREATED, response_model=DisplayUser)
def add_user(user: User, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.create_user(user)
    except ExistingUserExistsException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])

# update person linked with user
@router.put('/users/{id}/person')
def update_user_person(id: int, person_id: int, user_service: UserService = Depends(UserService), current_user: User = Depends(get_current_user)):
    try:
        return user_service.update_user_person(id, person_id)
    except NoUserException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except AlreadyExistPersonAssociatedWithUser as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])