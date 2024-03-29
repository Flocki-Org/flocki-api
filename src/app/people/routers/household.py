from fastapi import status, Depends, HTTPException, UploadFile, Query
from fastapi_pagination import Page, Params

from ..models.household import CreateHousehold, ViewHousehold, UpdateHousehold
from fastapi import APIRouter
from typing import List, Union

from ..models.people import BasicViewPerson
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

# get list of people that can be added to this household (excludes list of people already in the household,
# and sorts the list by last name, but prioritizes people with the same last name of the existing household
# with the household id as a parameter)
@router.get('/households/people', response_model=List[BasicViewPerson])
def get_people_not_in_household(household_id: int = Query(None, description="id of the household"),
                                name: Union[str, None] = None, surname: Union[str, None] = None,
                                household_service: HouseholdService = Depends(HouseholdService),
                                current_user: User = Depends(get_current_user)):
    try:
        people_response = household_service.get_people_not_in_household(household_id, name, surname)
        return people_response
    except NoHouseholdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household with that id does not exist")


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
def get_household_image(id: int, household_service: HouseholdService = Depends(HouseholdService)):
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
