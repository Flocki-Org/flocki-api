import uvicorn
from fastapi import FastAPI, Response, status, Depends, HTTPException
from app.models.person import Person, DisplayPerson
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
def get_person(id: int, response: Response, db: SessionLocal = Depends(get_db)):
    person = db.query(models.Person).filter(models.Person.id == id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person with that id does not exist")
    return db.query(models.Person).filter(models.Person.id == id).first()

@app.put('/person/')
def update_person(id:int, person: Person, db: SessionLocal = Depends(get_db)):
    personToUpdate = db.query(models.Person).filter(models.Person.id == id)
    if not personToUpdate.first():
        pass
    person.id = personToUpdate.first().id
    personDict = person.dict()
    personDict.pop('social_media_links', person.dict())
    personToUpdate.update(personDict)
    db.commit()
    return personDict

@app.post('/person', status_code = status.HTTP_201_CREATED)
def add_person(person: Person, response: Response, db: SessionLocal = Depends(get_db)):
    new_person = models.Person(
        first_name = person.first_name,
        last_name = person.last_name,
        email = person.email,
        mobile_number = person.mobile_number,
        date_of_birth = person.date_of_birth,
        gender = person.gender,
        marriage_date = person.marriage_date,
        marital_status = person.marital_status,
        registered_date = person.registered_date
    )
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    person.id = new_person.id
    return person

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)