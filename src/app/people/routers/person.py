from fastapi import status, Depends, HTTPException, UploadFile

from fastapi_pagination import Params, Page

from ..services.addressService import NoAddressException
from ..services.peopleService import PeopleService, NoPersonException, NoHouseholdExceptionForPersonCreation, \
    UnableToRemoveLeaderFromHouseholdException
from ...media.models.media import ViewImage
from ...media.services.mediaService import NoImageException
from ...people.models.people import CreatePerson, FullViewPerson, UpdatePerson
from fastapi import APIRouter
from typing import List, Union
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['People'])


@router.get('/people', response_model=Page[FullViewPerson])
def get_people(page: int = 1, page_size:int = 10, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    params: Params = Params(page=page, size=page_size)
    people_response = people_service.get_all(params)
    return people_response

#find people by email or first name and last name
@router.get('/people/find_by_email_or_names')
def find_by_email_or_names(email: Union[str, None] = None, first_name: Union[str, None] = None, last_name: Union[str, None] = None,
                           people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    return people_service.find_people_by_email_or_first_and_last_name(email, first_name, last_name)


@router.get('/people/{id}', response_model=FullViewPerson)
def get_person(id: int, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    person_response = people_service.get_by_id(id)
    if person_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

    return person_response


@router.put('/people/', response_model=FullViewPerson)
def update_person(id: int, person: UpdatePerson, people_service: PeopleService = Depends(PeopleService),
                  current_user: User = Depends(get_current_user)):
    try:
        person_response = people_service.update_person(id, person)
        if person_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        return person_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
    except (NoHouseholdExceptionForPersonCreation, UnableToRemoveLeaderFromHouseholdException, NoAddressException, NoImageException) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])



@router.get('/people/{id}/profile_image')
def get_person_profile_image(id: int, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    try:
        profile_image_response = people_service.get_profile_image_by_person_id(id)
        profile_image_response.headers['cache-control'] = 'max-age=20'
        if profile_image_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile image")

        return profile_image_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

@router.get('/people/{id}/profile_images', response_model=List[ViewImage])
def get_person_profile_images(id: int, people_service: PeopleService = Depends(PeopleService),
                current_user: User = Depends(get_current_user)):
    try:
        profile_image_responses = people_service.get_profile_images_by_person_id(id)
        if profile_image_responses is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile images")

        return profile_image_responses
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")


@router.put('/people/profile_image', response_model=ViewImage)
def update_person_with_profile_image(id: int, file: UploadFile, people_service: PeopleService = Depends(PeopleService),
                  current_user: User = Depends(get_current_user)):
    try:
        person_response = people_service.upload_profile_image(id, file)
        if person_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        return person_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
    except NoHouseholdExceptionForPersonCreation as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])


@router.post('/people', status_code=status.HTTP_201_CREATED, response_model=FullViewPerson)
def add_person(create_login: Union[bool, None], person: CreatePerson, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    try:
        return people_service.create_person(person, create_login)
    except (NoHouseholdExceptionForPersonCreation, UnableToRemoveLeaderFromHouseholdException, NoAddressException,
                NoImageException) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])

