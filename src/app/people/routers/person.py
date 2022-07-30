from fastapi import status, Depends, HTTPException
from ...people.models.people import Person, DisplayPerson
from fastapi import APIRouter
from typing import List
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models
from ...people.services.peopleFactory import PeopleFactory
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['People'])
peopleFactory = PeopleFactory()

@router.get('/people', response_model=List[DisplayPerson])
def get_people(db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    people_response = []
    people = db.query(models.Person).order_by(models.Person.last_name).all()
    for person in people:
        people_response.append(peopleFactory.createPersonFromPersonEntity(person_entity = person))

    return people_response

@router.get('/person/{id}', response_model=DisplayPerson)
def get_person(id: int, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    person_entity = db.query(models.Person).filter(models.Person.id == id).first()
    if not person_entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

    person_response = peopleFactory.createPersonFromPersonEntity(person_entity)

    return person_response

@router.put('/person/')
def update_person(id:int, person: Person, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    personToUpdate = db.query(models.Person).filter(models.Person.id == id)
    if not personToUpdate.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
    #For update requests the model is not expected to come in with an ID since it is passed in the URL.
    db_person = personToUpdate.first()
    person.id = db_person.id

    update_values = person.dict()
    smls = update_values.pop('social_media_links', person.dict())
    if smls is not None:
        existing_social_media_links = db.query(models.SocialMediaLink).filter(
            models.SocialMediaLink.person_id == person.id).all()
        if existing_social_media_links:
            for existing_sml in existing_social_media_links:
                db.query(models.SocialMediaLink).filter(
                    models.SocialMediaLink.id == existing_sml.id).delete(synchronize_session=False)

        for sml in smls:
            db.add(models.SocialMediaLink(person_id = person.id, type = sml['type'], url = sml['url']))

    addresses = update_values.pop('addresses', person.dict())
    if addresses is not None:
        existing_people_addresses = db.query(models.PeopleAddress).filter(
            models.PeopleAddress.person_id == person.id).all()
        if existing_people_addresses:
            for existing_people_address in existing_people_addresses:
                db.query(models.PeopleAddress).filter(
                    models.PeopleAddress.id == existing_people_address.id).delete(synchronize_session=False)

        # TODO consider querying DB if an address already exists with the given values. otherwise you will end up with
        # multiple rows in the DB for the same address
        for address in addresses:
            new_address = models.Address(
                type=address['type'],
                streetNumber=address['streetNumber'],
                street=address['street'],
                suburb=address['suburb'],
                city=address['city'],
                province=address['province'],
                country=address['country'],
                postalCode=address['postalCode'],
                latitude=address['latitude'],
                longitude=address['longitude'])

            db.add(models.PeopleAddress(
                address=new_address,
                person=db_person
            ))
    update_values.pop('household', person.dict())

    personToUpdate.update(update_values)
    db.commit()
    return get_person(person.id, db) #There probably is a more efficient way than to read this from the DB again.

@router.post('/person', status_code = status.HTTP_201_CREATED)
def add_person(person: Person, db: SessionLocal = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_person = peopleFactory.createPersonEntityFromPerson(person)

    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    person.id = new_person.id
    return person

