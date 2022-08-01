from fastapi import status, Depends, HTTPException

from ..models.household import DisplayHousehold, CreateHousehold, Household
from fastapi import APIRouter
from typing import List
from ..services.householdService import HouseholdService, NoHouseholdException
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Household'])

@router.get('/households', response_model=List[DisplayHousehold])
def get_households(household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    return household_service.get_all_households()

@router.get('/household/{id}', response_model=DisplayHousehold)
def get_household(id: int, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    try:
        return household_service.get_household_by_id(id)
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")

#adds a household to the DB
@router.post('/household', status_code = status.HTTP_201_CREATED, response_model=DisplayHousehold)
def add_household(household: CreateHousehold, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    #add household entity to database
    return household_service.add_household(household)
