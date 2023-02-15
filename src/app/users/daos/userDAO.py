from fastapi import Depends

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from src.app.database import SessionLocal, get_db
from src.app.users.models.database import models
from sqlalchemy import func

class UserDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all_users(self, params: Params = Params(page=1, size=100)) -> Page[models.User]:
        return paginate(self.db.query(models.User), params)

    def get_user_by_id(self, id) -> models.User:
        return self.db.query(models.User).filter(models.User.id == id).first()

    def create_user(self, new_user):
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return self.get_user_by_id(new_user.id)

    def update_user(self, user_id, update_values):
        if 'id' in update_values:
            del update_values['id']

        userToUpdate = self.db.query(models.User).filter(models.User.id == user_id)
        userToUpdate.update(update_values)
        self.db.commit()

    def get_user_by_name(self, username):
        return self.db.query(models.User).filter(func.lower(models.User.email) == func.lower(username)).first()

    def update_user_person(self, id, person_id):
        userToUpdate = self.db.query(models.User).filter(models.User.id == id)
        userToUpdate.update({'person_id': person_id})
        self.db.commit()


