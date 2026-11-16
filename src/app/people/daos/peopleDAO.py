from datetime import datetime, date
from typing import List

from fastapi import Depends

from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params

from sqlalchemy.orm import selectinload

from src.app.database import get_db, SessionLocal
from src.app.people.daos.peopleQuery import apply_people_filters, exclude_closed_records, month_day_filter
from src.app.people.models.database import models
from src.app.people.models.database.models import PersonImage

from sqlalchemy import or_, and_, extract, case, select

from src.app.utils.DateUtils import DateUtils


class PeopleDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def _profile_options(self):
        return (
            selectinload(models.Person.emails),
            selectinload(models.Person.phones),
            selectinload(models.Person.emergency_contacts),
            selectinload(models.Person.category_links).selectinload(models.PersonCategoryLink.category),
            selectinload(models.Person.service_type_links).selectinload(models.PersonServiceType.service_type),
        )

    def get_all(self, params: Params = Params(page=1, size=100)) -> Page[models.Person]:
        return paginate(self.db.query(models.Person).options(*self._profile_options())
                        .order_by(models.Person.last_name.asc(), models.Person.first_name.asc(),
                                  models.Person.date_of_birth.asc(), models.Person.id.asc())
                        , params)

    def get_person_by_id(self, id: int) -> models.Person:
        return self.db.query(models.Person).options(*self._profile_options()).filter(models.Person.id == id).first()

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
        values = dict(update_values)
        values.setdefault("updated_at", datetime.now())
        personToUpdate.update(values)
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
        current_date = DateUtils.get_current_datetime()
        query = self.db.query(models.Person).filter(
            and_(
                # ensure that date entered is more than or equal to the current year
                date.year >= current_date.year,
                # all people with birthdays in the next year before the date entered
                or_(
                    and_(
                        date.year > current_date.year,
                        or_(
                            extract('month', models.Person.date_of_birth) < date.month,
                            and_(
                                extract('month', models.Person.date_of_birth) == date.month,
                                extract('day', models.Person.date_of_birth) <= date.day
                            ),
                            extract('month', models.Person.date_of_birth) > current_date.month,
                        )
                    ),
                    # all people with birthdays in the current year before the date entered
                    and_(
                        date.year == current_date.year,
                        or_(
                            and_(
                                extract('month', models.Person.date_of_birth) > current_date.month,
                                extract('month', models.Person.date_of_birth) < date.month
                            ),
                            and_(
                                extract('month', models.Person.date_of_birth) > current_date.month,
                                extract('month', models.Person.date_of_birth) == date.month,
                                extract('day', models.Person.date_of_birth) <= date.day
                            ),
                            and_(
                                extract('month', models.Person.date_of_birth) == current_date.month,
                                extract('day', models.Person.date_of_birth) > current_date.day,
                                extract('day', models.Person.date_of_birth) <= date.day
                            ),
                            and_(
                                extract('month', models.Person.date_of_birth) == current_date.month,
                                extract('month', models.Person.date_of_birth) < date.month
                            )
                        ),
                    )
                )
            )
        ).order_by(models.Person.date_of_birth)

        return query.all()

    def find_people_with_anniversary_before_given_date(self, date: datetime.date) -> List[models.Person]:
        current_date = DateUtils.get_current_datetime()
        query = self.db.query(models.Person).filter(
            and_(
                # ensure that date entered is more than or equal to the current year
                date.year >= current_date.year,
                # all people with birthdays in the next year before the date entered
                or_(
                    and_(
                        date.year > current_date.year,
                        or_(
                            extract('month', models.Person.marriage_date) < date.month,
                            and_(
                                extract('month', models.Person.marriage_date) == date.month,
                                extract('day', models.Person.marriage_date) <= date.day
                            ),
                            extract('month', models.Person.marriage_date) > current_date.month,
                        )
                    ),
                    # all people with birthdays in the current year before the date entered
                    and_(
                        date.year == current_date.year,
                        or_(
                            and_(
                                extract('month', models.Person.marriage_date) > current_date.month,
                                extract('month', models.Person.marriage_date) < date.month
                            ),
                            and_(
                                extract('month', models.Person.marriage_date) > current_date.month,
                                extract('month', models.Person.marriage_date) == date.month,
                                extract('day', models.Person.marriage_date) <= date.day
                            ),
                            and_(
                                extract('month', models.Person.marriage_date) == current_date.month,
                                extract('day', models.Person.marriage_date) > current_date.day,
                                extract('day', models.Person.marriage_date) <= date.day
                            ),
                            and_(
                                extract('month', models.Person.marriage_date) == current_date.month,
                                extract('month', models.Person.marriage_date) < date.month
                            )
                        ),
                    )
                )
            )
        ).order_by(models.Person.marriage_date)

        return query.all()

    def find_people_with_name_or_surname_starting_with(self, name, surname) -> List[models.Person]:
        # Create a case statement to calculate the sorting priority.
        surname_match = case(
            [
                (and_(models.Person.last_name.ilike(f"{surname}%"), models.Person.first_name.ilike(f"{name}%")),
                 1) if name and surname else (False, 1),
                (models.Person.last_name.ilike(f"{surname}%"), 2) if surname else (False, 2),
            ],
            else_=3
        )

        # Query and order the results based on the calculated priority.
        people_query = self.db.query(models.Person)

        if name and surname:
            people_query = people_query.filter(models.Person.first_name.ilike(f"{name}%"),
                                               models.Person.last_name.ilike(f"{surname}%"))
        elif name:
            people_query = people_query.filter(
                or_(models.Person.first_name.ilike(f"{name}%"), models.Person.last_name.ilike(f"{name}%")))
        elif surname:
            people_query = people_query.filter(models.Person.last_name.ilike(f"{surname}%"))

        people = people_query.order_by(surname_match, models.Person.last_name, models.Person.first_name).all()

        return people

    def search(self, filters, params: Params = Params(page=1, size=100)):
        query = self.db.query(models.Person).options(*self._profile_options())
        query = apply_people_filters(query, filters)
        return paginate(query, params)

    def find_by_report(self, kind: str, days: int = 30):
        today = datetime.now().date()
        query = self.db.query(models.Person).options(*self._profile_options())
        query = exclude_closed_records(query)
        if kind == "birthdays":
            query = query.filter(models.Person.date_of_birth.isnot(None))
            query = query.filter(month_day_filter(models.Person.date_of_birth, today, days))
        elif kind == "anniversaries":
            query = query.filter(models.Person.marriage_date.isnot(None))
            query = query.filter(month_day_filter(models.Person.marriage_date, today, days))
        elif kind == "without_email":
            query = query.filter(and_(
                or_(models.Person.email.is_(None), models.Person.email == ""),
                ~models.Person.emails.any(),
            ))
        elif kind == "without_mobile":
            query = query.filter(and_(
                or_(models.Person.mobile_number.is_(None), models.Person.mobile_number == ""),
                ~models.Person.phones.any(models.PersonPhone.phone_type == "mobile"),
            ))
        elif kind == "without_group":
            from src.app.groups.models.database.models import GroupMembership
            query = query.filter(~models.Person.id.in_(
                select(GroupMembership.person_id).where(GroupMembership.status == "active")
            ))
        elif kind == "inactive":
            query = query.filter(models.Person.lifecycle_status == "inactive")
        return query.order_by(models.Person.last_name.asc(), models.Person.first_name.asc()).all()

    def add_status_history(self, person_id, field_name, previous_value, new_value, reason=None, actor_user_id=None):
        self.db.add(models.PersonStatusHistory(
            person_id=person_id,
            field_name=field_name,
            previous_value=previous_value,
            new_value=new_value,
            reason=reason,
            changed_by_user_id=actor_user_id,
        ))

    def status_history(self, person_id):
        return (
            self.db.query(models.PersonStatusHistory)
            .filter(models.PersonStatusHistory.person_id == person_id)
            .order_by(models.PersonStatusHistory.changed_at.desc())
            .all()
        )

    def replace_emails(self, person, emails):
        for existing in list(person.emails):
            self.db.delete(existing)
        self.db.flush()
        for email in emails:
            email.person = person
            self.db.add(email)

    def replace_phones(self, person, phones):
        for existing in list(person.phones):
            self.db.delete(existing)
        self.db.flush()
        for phone in phones:
            phone.person = person
            self.db.add(phone)

    def replace_emergency_contacts(self, person, contacts):
        for existing in list(person.emergency_contacts):
            self.db.delete(existing)
        self.db.flush()
        for contact in contacts:
            contact.person = person
            self.db.add(contact)

    def list_relationships(self, person_id):
        return (
            self.db.query(models.PersonRelationship)
            .filter(or_(
                models.PersonRelationship.person_id == person_id,
                models.PersonRelationship.related_person_id == person_id,
            ))
            .all()
        )

    def find_relationship(self, person_id, related_person_id, relationship_type, inverse_type):
        return (
            self.db.query(models.PersonRelationship)
            .filter(or_(
                and_(
                    models.PersonRelationship.person_id == person_id,
                    models.PersonRelationship.related_person_id == related_person_id,
                    models.PersonRelationship.relationship_type == relationship_type,
                ),
                and_(
                    models.PersonRelationship.person_id == related_person_id,
                    models.PersonRelationship.related_person_id == person_id,
                    models.PersonRelationship.relationship_type == inverse_type,
                ),
            ))
            .first()
        )

    def add_relationship(self, relationship):
        self.db.add(relationship)
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def get_relationship(self, relationship_id):
        return self.db.query(models.PersonRelationship).filter(models.PersonRelationship.id == relationship_id).first()

    def delete_relationship(self, relationship):
        self.db.delete(relationship)
        self.db.commit()
