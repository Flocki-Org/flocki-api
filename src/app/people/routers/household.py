from fastapi import status, Depends, HTTPException, UploadFile

from ..models.household import DisplayHousehold, CreateHousehold, Household, DisplayHouseholdImage
from fastapi import APIRouter
from typing import List
from ..services.householdService import HouseholdService, NoHouseholdException
from ...media.models.media import DisplayImage
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

@router.get('/household/{id}/household_image')
def get_household_image(id: int, household_service: HouseholdService = Depends(HouseholdService),
               current_user: User = Depends(get_current_user)):
    try:
        household_image_response = household_service.get_household_image_by_household_id(id)
        if household_image_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile image")

        return household_image_response
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")

@router.get('/household/{id}/profile_images', response_model=List[DisplayImage])
def get_household_images(id: int, household_service: HouseholdService = Depends(HouseholdService),
                current_user: User = Depends(get_current_user)):
    try:
        household_image_responses = household_service.get_household_images_by_household_id(id)
        if household_image_responses is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No household images")

        return household_image_responses
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")


@router.put('/household/household_image', response_model=DisplayHouseholdImage)
def update_household_with_image(id: int, file: UploadFile, household_service: HouseholdService = Depends(HouseholdService),
                  current_user: User = Depends(get_current_user)):
    try:
        household_response = household_service.upload_household_image(id, file)
        if household_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No household images")
        return household_response
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")
