from fastapi import Depends
from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models

class PeopleDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all(self):
        return self.db.query(models.Person).order_by(models.Person.last_name).all()

    def get_person_by_id(self, id: int):
        return self.db.query(models.Person).filter(models.Person.id == id).first()

    def update_person(self, person_id, update_values):
        personToUpdate = self.db.query(models.Person).filter(models.Person.id == person_id)
        personToUpdate.update(update_values)
        self.db.commit()

    def get_existing_social_media_links(self, person_id: int):
        return self.db.query(models.SocialMediaLink).filter(
            models.SocialMediaLink.person_id == person_id).all()

    def delete_social_media_link(self, existing_sml_id):
        self.db.query(models.SocialMediaLink).filter(
            models.SocialMediaLink.id == existing_sml_id).delete(synchronize_session=False)

    def create_social_media_link(self, person_id, type: str, url: str):
        self.db.add(models.SocialMediaLink(person_id=person_id, type=type, url=url))

    def create_person(self, new_person):
        self.db.add(new_person)
        self.db.commit()
        self.db.refresh(new_person)
        return new_person
