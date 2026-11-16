from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.people.models.database import models


class CategoryDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def list_categories(self, include_inactive=False):
        query = self.db.query(models.PeopleCategory).order_by(models.PeopleCategory.name.asc())
        if not include_inactive:
            query = query.filter(models.PeopleCategory.active.is_(True))
        return query.all()

    def get(self, category_id):
        return self.db.query(models.PeopleCategory).filter(models.PeopleCategory.id == category_id).first()

    def get_by_name(self, name):
        return self.db.query(models.PeopleCategory).filter(models.PeopleCategory.name == name).first()

    def add(self, category):
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def save(self, category):
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category):
        self.db.delete(category)
        self.db.commit()

    def in_use(self, category_id):
        return (
            self.db.query(models.PersonCategoryLink)
            .filter(models.PersonCategoryLink.category_id == category_id)
            .first()
            is not None
        )

    def replace_for_person(self, person, category_ids):
        for link in list(person.category_links):
            self.db.delete(link)
        self.db.flush()
        for category_id in dict.fromkeys(category_ids):
            self.db.add(models.PersonCategoryLink(person_id=person.id, category_id=category_id))


class ReferenceDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def list_values(self, domain=None, include_inactive=False):
        query = self.db.query(models.ReferenceValue).order_by(
            models.ReferenceValue.domain.asc(),
            models.ReferenceValue.display_order.asc(),
        )
        if domain:
            query = query.filter(models.ReferenceValue.domain == domain)
        if not include_inactive:
            query = query.filter(models.ReferenceValue.active.is_(True))
        return query.all()

    def get(self, value_id):
        return self.db.query(models.ReferenceValue).filter(models.ReferenceValue.id == value_id).first()

    def get_by_domain_value(self, domain, value):
        return (
            self.db.query(models.ReferenceValue)
            .filter(models.ReferenceValue.domain == domain, models.ReferenceValue.value == value)
            .first()
        )

    def add(self, row):
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row):
        self.db.commit()
        self.db.refresh(row)
        return row


class ServiceTypeDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def list_types(self, include_inactive=False):
        query = self.db.query(models.ServiceType).order_by(models.ServiceType.name.asc())
        if not include_inactive:
            query = query.filter(models.ServiceType.active.is_(True))
        return query.all()

    def get(self, service_type_id):
        return self.db.query(models.ServiceType).filter(models.ServiceType.id == service_type_id).first()

    def add(self, row):
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row):
        self.db.commit()
        self.db.refresh(row)
        return row

    def replace_for_person(self, person, service_type_ids):
        for link in list(person.service_type_links):
            self.db.delete(link)
        self.db.flush()
        for service_type_id in dict.fromkeys(service_type_ids):
            self.db.add(models.PersonServiceType(person_id=person.id, service_type_id=service_type_id))
