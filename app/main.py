from fastapi import FastAPI, Response, status
from .models.person import Person

people = {}
app = FastAPI()

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api sss'

@app.get('/person/{id}')
def getPerson(id: int):
    return people[id]

@app.post('/person')
def add_person(person: Person, response: Response):
    people[person.id] = person
    response.status_code = status.HTTP_201_CREATED
    return response