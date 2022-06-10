import uvicorn
from fastapi import FastAPI, Response, status, Depends, HTTPException
from app.models.person import Person, DisplayPerson, SocialMediaLink
from app.database import engine, SessionLocal
from app.models.database import models
from typing import List

models.Base.metadata.create_all(engine)

people = {}
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api.'

@app.get('/people', response_model=List[DisplayPerson])
def get_people(db: SessionLocal = Depends(get_db)):
    return db.query(models.Person).all()

@app.get('/person/{id}', response_model=DisplayPerson)
def get_person(id: int, db: SessionLocal = Depends(get_db)):
    person_entity = db.query(models.Person).filter(models.Person.id == id).first()
    if not person_entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")

    person_response = Person(
        id = person_entity.id,
        first_name = person_entity.first_name,
        last_name = person_entity.last_name,
        email = person_entity.email,
        mobile_number = person_entity.mobile_number,
        date_of_birth = person_entity.date_of_birth,
        gender = person_entity.gender,
        marriage_date = person_entity.marriage_date,
        marital_status = person_entity.marital_status,
        registered_date = person_entity.registered_date,
    )
    if person_entity.social_media_links:
        for sml in person_entity.social_media_links:
            sml_response = SocialMediaLink(type=sml.type, url=sml.url)
            person_response.social_media_links.append(sml_response)

    return person_response

@app.put('/person/')
def update_person(id:int, person: Person, db: SessionLocal = Depends(get_db)):
    personToUpdate = db.query(models.Person).filter(models.Person.id == id)
    if not personToUpdate.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
    #For update requests the model is not expected to come in with an ID since it is passed in the URL.
    person.id = personToUpdate.first().id

    update_values = person.dict()
    smls = update_values.pop('social_media_links', person.dict())
    if smls is not None:
        print("Got here")
        existing_social_media_links = db.query(models.SocialMediaLinks).filter(models.SocialMediaLinks.person_id == person.id).all()
        if existing_social_media_links:
            for existing_sml in existing_social_media_links:
                db.query(models.SocialMediaLinks).filter(models.SocialMediaLinks.id == existing_sml.id).delete(synchronize_session=False)

        for sml in smls:
            db.add(models.SocialMediaLinks(person_id = person.id, type = sml['type'], url = sml['url']))

    personToUpdate.update(update_values)
    db.commit()
    return get_person(person.id, db) #There probably is a more efficient way than to read this from the DB again.

@app.post('/person', status_code = status.HTTP_201_CREATED)
def add_person(person: Person, db: SessionLocal = Depends(get_db)):
    new_person = models.Person(
        first_name = person.first_name,
        last_name = person.last_name,
        email = person.email,
        mobile_number = person.mobile_number,
        date_of_birth = person.date_of_birth,
        gender = person.gender,
        marriage_date = person.marriage_date,
        marital_status = person.marital_status,
        registered_date = person.registered_date,
    )

    if person.social_media_links:
        for sml in person.social_media_links:
            new_sml = models.SocialMediaLinks(type=sml.type, url=sml.url)
            new_person.social_media_links.append(new_sml)

    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    person.id = new_person.id
    return person

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)