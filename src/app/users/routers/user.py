from fastapi import status, Depends, HTTPException

from .login import get_current_user
from ...users.models.user import User, DisplayUser
from fastapi import APIRouter
from typing import List
from src.app.database import get_db, SessionLocal
from src.app.users.models.database import models
from ...users.services.userFactory import createUserEntityFromUser, createUserFromUserEntity, hash_pwd
router = APIRouter()

@router.get('/users', response_model=List[DisplayUser])
def get_users(db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    users_response = []
    users = db.query(models.User).order_by(models.User.last_name).all()
    for user in users:
        users_response.append(createUserFromUserEntity(user))

    return users_response

@router.get('/user/{id}', response_model=DisplayUser)
def get_user(id: int, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_entity = db.query(models.User).filter(models.User.id == id).first()
    if not user_entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that id does not exist")

    user_response = createUserFromUserEntity(user_entity)

    return user_response

@router.put('/user/')
def update_user(id:int, user: User, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    userToUpdate = db.query(models.User).filter(models.User.id == id)
    if not userToUpdate.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that id does not exist")
    #For update requests the model is not expected to come in with an ID since it is passed in the URL.
    update_values = user.dict()
    update_values['id'] = id
    if 'password' in update_values:
        update_values['password'] = hash_pwd(update_values['password'])
    userToUpdate.update(update_values)
    db.commit()
    return get_user(id, db) #There probably is a more efficient way than to read this from the DB again.

@router.post('/user', status_code = status.HTTP_201_CREATED, response_model=DisplayUser)
def add_user(user: User, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_user = createUserEntityFromUser(user)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user.id = new_user.id
    return user

