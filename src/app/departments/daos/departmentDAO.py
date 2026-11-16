from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.departments.models.database import models


class DepartmentDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def list_departments(self, include_inactive=False):
        query = self.db.query(models.Department).order_by(models.Department.name.asc())
        if not include_inactive:
            query = query.filter(models.Department.active.is_(True))
        return query.all()

    def get(self, department_id):
        return self.db.query(models.Department).filter(models.Department.id == department_id).first()

    def add(self, department):
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def save(self, department):
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete(self, department):
        self.db.delete(department)
        self.db.commit()

    def child_count(self, department_id):
        return self.db.query(models.Department).filter(models.Department.parent_id == department_id).count()

    def person_link(self, department_id, person_id):
        return (
            self.db.query(models.DepartmentPerson)
            .filter(
                models.DepartmentPerson.department_id == department_id,
                models.DepartmentPerson.person_id == person_id,
            )
            .first()
        )

    def add_person(self, link):
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete_person(self, link):
        self.db.delete(link)
        self.db.commit()

    def people(self, department_id):
        return (
            self.db.query(models.DepartmentPerson)
            .filter(models.DepartmentPerson.department_id == department_id)
            .all()
        )

    def departments_for_person(self, person_id):
        return (
            self.db.query(models.DepartmentPerson)
            .filter(models.DepartmentPerson.person_id == person_id)
            .all()
        )

    def group_link(self, department_id, group_id):
        return (
            self.db.query(models.DepartmentGroup)
            .filter(
                models.DepartmentGroup.department_id == department_id,
                models.DepartmentGroup.group_id == group_id,
            )
            .first()
        )

    def add_group(self, link):
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete_group(self, link):
        self.db.delete(link)
        self.db.commit()

    def groups(self, department_id):
        return self.db.query(models.DepartmentGroup).filter(models.DepartmentGroup.department_id == department_id).all()
