from fastapi import status, Depends, HTTPException

from ..models.household import DisplayHousehold, CreateHousehold
from fastapi import APIRouter
from typing import List
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models
from ...people.services.householdFactory import HouseholdFactory
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Household'])
householdFactory = HouseholdFactory()

@router.get('/household', response_model=List[DisplayHousehold])
def get_households(db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    households = db.query(models.Household).all()
    households_response = []
    for h in households:
        households_response.append(householdFactory.createHouseholdFromHouseholdEntity(h))

    return households_response

@router.get('/household/{id}', response_model=DisplayHousehold)
def get_household(id: int, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    household_entity = db.query(models.Household).filter(models.Household.id == id).first()
    if not household_entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")

    return householdFactory.createHouseholdFromHouseholdEntity(household_entity)


#adds a person to the database
@router.post('/household', status_code = status.HTTP_201_CREATED)
def add_person(household: CreateHousehold, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    #add household entity to database
    people_models = []
    for person in household.people:
        person_entity = db.query(models.Person).filter(models.Person.id == person.id).first()
        if not person_entity:
            raise Exception(f"Person does not exist with ID: %{person.id}")

        people_models.append(person_entity)

    new_houshold = householdFactory.createHouseholdEntityFromHousehold(household, people_models)
    db.add(new_houshold)
    db.commit()
    db.refresh(new_houshold)
    household.id = new_houshold.id
    return household