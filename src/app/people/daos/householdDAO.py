from fastapi import Depends
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models

class HouseholdDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db=db

    def get_all_households(self):
        return self.db.query(models.Household).all()

    def get_household_by_id(self, id):
        return self.db.query(models.Household).filter(models.Household.id == id).first()

    def add_household(self, new_household):
        self.db.add(new_household)
        self.db.commit()
        self.db.refresh(new_household)
        return self.get_household_by_id(new_household.id)
