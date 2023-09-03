from fastapi import status, Depends, HTTPException, UploadFile
from fastapi_pagination import Page, Params

from ..models.household import CreateHousehold, ViewHousehold, UpdateHousehold
from fastapi import APIRouter
from typing import List
from ..services.householdService import HouseholdService, NoHouseholdException
from ..services.peopleService import NoPersonException
from ...media.models.media import ViewMediaItem
from ...media.services.mediaService import NoMediaItemException
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Household'])

@router.get('/households', response_model=Page[ViewHousehold])
def get_households(page: int = 1, page_size:int = 10, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    params: Params = Params(page=page, size=page_size)
    return household_service.get_all_households(params=params)

@router.get('/households/{id}', response_model=ViewHousehold)
def get_household(id: int, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    try:
        return household_service.get_household_by_id(id)
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")

#adds a household to the DB
@router.post('/households', status_code = status.HTTP_201_CREATED, response_model=ViewHousehold)
def add_household(household: CreateHousehold, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    #add household entity to database
    try:
        return household_service.add_household(household)
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])
    except NoMediaItemException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0])

@router.put('/households', response_model=ViewHousehold)
def update_household(id: int, household: UpdateHousehold, household_service: HouseholdService = Depends(HouseholdService), current_user: User = Depends(get_current_user)):
    try:
        return household_service.update_household(id, household)
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

@router.get('/households/{id}/household_image')
def get_household_image(id: int, household_service: HouseholdService = Depends(HouseholdService),
               current_user: User = Depends(get_current_user)):
    try:
        household_image_response = household_service.get_household_image_by_household_id(id)
        if household_image_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile image")

        return household_image_response
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")

@router.get('/households/{id}/profile_images', response_model=List[ViewMediaItem])
def get_household_images(id: int, household_service: HouseholdService = Depends(HouseholdService),
                current_user: User = Depends(get_current_user)):
    try:
        household_image_responses = household_service.get_household_images_by_household_id(id)
        if household_image_responses is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No household media")

        return household_image_responses
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")


@router.put('/households/household_image', response_model=ViewMediaItem)
def update_household_with_image(id: int, file: UploadFile, household_service: HouseholdService = Depends(HouseholdService),
                  current_user: User = Depends(get_current_user)):
    try:
        household_response = household_service.upload_household_image(id, file)
        if household_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No household media")
        return household_response
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")
