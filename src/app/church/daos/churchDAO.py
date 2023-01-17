from fastapi import Depends

from src.app.church.models.church import CreateChurch, UpdateChurch
from src.app.database import get_db, SessionLocal

from src.app.church.models.database import models

class ChurchDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db=db

    def create_church(self, new_church: CreateChurch) -> models.Church:
        #don't allow more than one church in the database
        if self.get_church() is not None:
            raise Exception("Church already exists")

        self.db.add(new_church)
        self.db.commit()
        self.db.refresh(new_church)

        return new_church

    def get_church(self) -> models.Church:
        return self.db.query(models.Church).first()

    def update_church(self, update_values):
        church_entity = self.db.query(models.Church).first()
        church_entity_to_update = self.db.query(models.Church).filter(models.Church.id == church_entity.id)
        if church_entity is None:
            raise Exception("Church does not exist")
        church_entity_to_update.update(update_values)
        self.db.commit()

