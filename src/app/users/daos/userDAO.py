from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.users.models.database import models
from sqlalchemy import func

class UserDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all_users(self):
        return self.db.query(models.User).all()

    def get_user_by_id(self, id):
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
