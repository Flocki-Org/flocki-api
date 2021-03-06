from fastapi import status, Depends, HTTPException

from ..services.peopleService import PeopleService, NoPersonException
from ...people.models.people import Person, DisplayPerson
from fastapi import APIRouter
from typing import List
from ...people.factories.peopleFactory import PeopleFactory
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['People'])
peopleFactory = PeopleFactory()


@router.get('/people', response_model=List[DisplayPerson])
def get_people(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    people_response = people_service.get_all()
    return people_response


@router.get('/person/{id}', response_model=DisplayPerson)
def get_person(id: int, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    person_response = people_service.get_by_id(id)
    if person_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

    return person_response


@router.put('/person/', response_model=DisplayPerson)
def update_person(id: int, person: Person, people_service: PeopleService = Depends(PeopleService),
                  current_user: User = Depends(get_current_user)):
    try:
        person_response = people_service.update_person(id, person)
        if person_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
        return person_response
    except NoPersonException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")


@router.post('/person', status_code=status.HTTP_201_CREATED, response_model=DisplayPerson)
def add_person(person: Person, people_service: PeopleService = Depends(PeopleService),
               current_user: User = Depends(get_current_user)):
    return people_service.create_person(person)
