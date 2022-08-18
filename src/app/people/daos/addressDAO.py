from fastapi import Depends
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models

class AddressDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_address_by_id(self, address_id):
        return self.db.query(models.Address).filter(
            models.Address.id == address_id).first()

    def get_existing_addresses_for_person(self, person_id):
        return self.db.query(models.PeopleAddress).filter(
            models.PeopleAddress.person_id == person_id).all()

    def delete_address(self, address_id):
        self.db.query(models.PeopleAddress).filter(
            models.PeopleAddress.id == address_id).delete(synchronize_session=False)

    def update_address(self, address_id, update_values):
        address_entity = self.db.query(models.Address).filter(models.Address.id == address_id)
        address_entity.update(update_values)
        self.db.commit()

    def create_address(self, new_address):
        self.db.add(new_address)
        self.db.commit()
        self.db.refresh(new_address)
        return new_address

    def create_address_linked_to_person(self, address, person):
        self.db.add(models.PeopleAddress(
            address=address,
            person=person
        ))

    def get_all_addresses(self):
        return self.db.query(models.Address).order_by(models.Address.city, models.Address.suburb, models.Address.street).all()

    def find_address(self, type, street_number, street, suburb, city, province, country, postal_code):
        return self.db.query(models.Address).filter(
            models.Address.type == type,
            models.Address.streetNumber == street_number,
            models.Address.street == street,
            models.Address.suburb == suburb,
            models.Address.city == city,
            models.Address.province == province if province is not None else True,
            models.Address.country == country if country is not None else True,
            models.Address.postalCode == postal_code if postal_code is not None else True).first()

