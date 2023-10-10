from datetime import datetime
from typing import List

from fastapi import Depends

from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params

from src.app.database import get_db, SessionLocal
from src.app.people.models.database import models
from src.app.people.models.database.models import PersonImage

from sqlalchemy import or_, and_, extract


class PeopleDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all(self, params: Params = Params(page=1, size=100)) -> Page[models.Person]:
        return paginate(self.db.query(models.Person)
                        .order_by(models.Person.last_name.asc(), models.Person.first_name.asc(),
                                  models.Person.date_of_birth.asc(), models.Person.id.asc())
                        , params)

    def get_person_by_id(self, id: int) -> models.Person:
        return self.db.query(models.Person).filter(models.Person.id == id).first()

    def find_people_by_email_or_first_name_and_last_name(self, email: str, first_name: str, last_name: str) -> List[
        models.Person]:
        return self.db.query(models.Person).filter(
            or_(models.Person.email == email, and_(models.Person.first_name == first_name,
                                                   models.Person.last_name == last_name))).order_by(
            models.Person.id).all()

    def update_person(self, person_id, update_values, image_entity=None):
        personToUpdate = self.db.query(models.Person).filter(models.Person.id == person_id)
        if image_entity is not None:
            person_image = PersonImage(
                person=personToUpdate.first(),
                image=image_entity,
                created=datetime.now(),
            )
            self.db.add(person_image)
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

    # TODO figure out what to do with household_entities
    # TODO create person should be responsible for creating social media links as well as household entities so rollback can happen in one method
    def create_person(self, new_person, image_entity=None):

        self.db.add(new_person)
        self.db.commit()
        self.db.refresh(new_person)

        if image_entity is not None:
            person_image = PersonImage(
                person=new_person,
                image=image_entity,
                created=datetime.now(),
            )
            self.db.add(person_image)
            self.db.commit()
            self.db.refresh(new_person)

        return new_person

    def add_person_image(self, personToUpdate, image_entity):
        person_image = PersonImage(
            person=personToUpdate,
            image=image_entity,
            created=datetime.now(),
        )
        self.db.add(person_image)
        self.db.commit()

    def find_people_with_birthday_before_given_date(self, date: datetime.date) -> List[models.Person]:
        current_date = datetime.now().date()
        query = self.db.query(models.Person).filter(
            and_(
                or_(
                    current_date.year < date.year,
                    extract('month', models.Person.date_of_birth) < date.month,
                    and_(
                        extract('month', models.Person.date_of_birth) == date.month,
                        extract('day', models.Person.date_of_birth) < date.day
                    )
                ),
                current_date.year <= date.year,
                or_(

                    extract('month', models.Person.date_of_birth) > current_date.month,
                    and_(
                        extract('month', models.Person.date_of_birth) == current_date.month,
                        extract('day', models.Person.date_of_birth) > current_date.day
                    )
                )
            )
        ).order_by(models.Person.date_of_birth)
        return query.all()
