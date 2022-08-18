from fastapi import status, Depends, HTTPException, UploadFile

from ..services.peopleService import PeopleService, NoPersonException
from ...media.models.media import ViewImage
from ...people.models.people import CreatePerson, FullViewPerson, UpdatePerson
from fastapi import APIRouter
from typing import List
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['People'])


@router.get('/people', response_model=List[FullViewPerson])
def get_people(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    people_response = people_service.get_all()
    return people_response


@router.get('/person/{id}', response_model=FullViewPerson)
def get_person(id: int, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    person_response = people_service.get_by_id(id)
    if person_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

    return person_response


@router.put('/person/', response_model=FullViewPerson)
def update_person(id: int, person: UpdatePerson, people_service: PeopleService = Depends(PeopleService),
                  current_user: User = Depends(get_current_user)):
    try:
        person_response = people_service.update_person(id, person)
        if person_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        return person_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

@router.get('/person/{id}/profile_image')
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

@router.get('/person/{id}/profile_images', response_model=List[ViewImage])
def get_person_profile_images(id: int, people_service: PeopleService = Depends(PeopleService),
                current_user: User = Depends(get_current_user)):
    try:
        profile_image_responses = people_service.get_profile_images_by_person_id(id)
        if profile_image_responses is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile images")

        return profile_image_responses
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

@router.put('/person/profile_image', response_model=ViewImage)
def update_person_with_profile_image(id: int, file: UploadFile, people_service: PeopleService = Depends(PeopleService),
                  current_user: User = Depends(get_current_user)):
    try:
        person_response = people_service.upload_profile_image(id, file)
        if person_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        return person_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

@router.post('/person', status_code=status.HTTP_201_CREATED, response_model=FullViewPerson)
def add_person(person: CreatePerson, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    return people_service.create_person(person)
