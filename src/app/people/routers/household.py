from fastapi import status, Depends, HTTPException

from ..models.househould import DisplayHousehold
from ...people.models.person import Person, DisplayPerson
from fastapi import APIRouter
from typing import List
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models
from...people.services.householdFactory import createHouseholdFromHouseholdEntity
    #, createPersonEntityFromPerson
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Household'])

@router.get('/household', response_model=List[DisplayHousehold])
def get_households(db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    households = db.query(models.Household).all()
    households_response = []
    for h in households:
        households_response.append(createHouseholdFromHouseholdEntity(h))

    return households_response


