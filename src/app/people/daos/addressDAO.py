from fastapi import Depends
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models

class AddressDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_existing_addresses_for_person(self, person_id):
        return self.db.query(models.PeopleAddress).filter(
            models.PeopleAddress.person_id == person_id).all()

    def delete_address(self, address_id):
        self.db.query(models.PeopleAddress).filter(
            models.PeopleAddress.id == address_id).delete(synchronize_session=False)

    def create_address(self, address, person):
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

        self.db.add(models.PeopleAddress(
            address=new_address,
            person=person
        ))

