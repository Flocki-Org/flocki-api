from typing import Optional

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from src.app.departments.daos.departmentDAO import DepartmentDAO
from src.app.departments.models.database import models
from src.app.groups.daos.groupDAO import GroupDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.services.peopleService import NoPersonException


class NoDepartmentException(Exception):
    pass


class DepartmentCycleException(Exception):
    pass


class DepartmentInUseException(Exception):
    pass


class DepartmentInput(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    active: bool = True

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Children's Ministry", "description": "Sunday and midweek"}}
    )


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    active: Optional[bool] = None


class DepartmentPersonInput(BaseModel):
    person_id: int
    notes: Optional[str] = None


class DepartmentGroupInput(BaseModel):
    group_id: int


class DepartmentView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    active: bool = True
    child_ids: list[int] = []


class DepartmentService:
    def __init__(self, department_dao: DepartmentDAO = Depends(DepartmentDAO),
                 people_dao: PeopleDAO = Depends(PeopleDAO), group_dao: GroupDAO = Depends(GroupDAO)):
        self.department_dao = department_dao
        self.people_dao = people_dao
        self.group_dao = group_dao

    def list_departments(self, include_inactive=False):
        rows = self.department_dao.list_departments(include_inactive)
        return [self._view(row, rows) for row in rows]

    def get(self, department_id):
        department = self._require(department_id)
        return self._view(department, self.department_dao.list_departments(include_inactive=True))

    def create(self, payload: DepartmentInput):
        self._validate_parent(None, payload.parent_id)
        department = models.Department(
            name=payload.name.strip(),
            description=payload.description,
            parent_id=payload.parent_id,
            active=payload.active,
        )
        return self._view(self.department_dao.add(department), self.department_dao.list_departments(True))

    def update(self, department_id, payload: DepartmentUpdate):
        department = self._require(department_id)
        data = payload.model_dump(exclude_unset=True)
        if "parent_id" in data:
            self._validate_parent(department_id, data["parent_id"])
        for key, value in data.items():
            setattr(department, key, value)
        return self._view(self.department_dao.save(department), self.department_dao.list_departments(True))

    def delete(self, department_id):
        department = self._require(department_id)
        if self.department_dao.child_count(department_id):
            raise DepartmentInUseException("Move or remove child departments first")
        if self.department_dao.people(department_id) or self.department_dao.groups(department_id):
            raise DepartmentInUseException("Remove people and groups from this department first")
        self.department_dao.delete(department)

    def add_person(self, department_id, payload: DepartmentPersonInput):
        self._require(department_id)
        if self.people_dao.get_person_by_id(payload.person_id) is None:
            raise NoPersonException(f"No person with the following ID: {payload.person_id}")
        if self.department_dao.person_link(department_id, payload.person_id):
            raise DepartmentInUseException("That person is already in this department")
        self.department_dao.add_person(models.DepartmentPerson(
            department_id=department_id,
            person_id=payload.person_id,
            notes=payload.notes,
        ))
        return self.get(department_id)

    def remove_person(self, department_id, person_id):
        link = self.department_dao.person_link(department_id, person_id)
        if link is None:
            raise NoPersonException("That person is not in this department")
        self.department_dao.delete_person(link)
        return self.get(department_id)

    def add_group(self, department_id, payload: DepartmentGroupInput):
        self._require(department_id)
        if self.group_dao.get(payload.group_id) is None:
            raise NoDepartmentException("Group does not exist")
        if self.department_dao.group_link(department_id, payload.group_id):
            raise DepartmentInUseException("That group is already in this department")
        self.department_dao.add_group(models.DepartmentGroup(department_id=department_id, group_id=payload.group_id))
        return self.get(department_id)

    def remove_group(self, department_id, group_id):
        link = self.department_dao.group_link(department_id, group_id)
        if link is None:
            raise NoDepartmentException("That group is not in this department")
        self.department_dao.delete_group(link)
        return self.get(department_id)

    def for_person(self, person_id):
        links = self.department_dao.departments_for_person(person_id)
        results = []
        for link in links:
            department = self.department_dao.get(link.department_id)
            if department is not None:
                results.append({
                    "department_id": department.id,
                    "name": department.name,
                    "parent_id": department.parent_id,
                })
        return results

    def _require(self, department_id):
        department = self.department_dao.get(department_id)
        if department is None:
            raise NoDepartmentException("Department does not exist")
        return department

    def _validate_parent(self, department_id, parent_id):
        if parent_id is None:
            return
        if department_id is not None and parent_id == department_id:
            raise DepartmentCycleException("A department cannot be its own parent")
        seen = set()
        current = parent_id
        while current is not None:
            if current in seen or current == department_id:
                raise DepartmentCycleException("That parent would create a cycle")
            seen.add(current)
            parent = self.department_dao.get(current)
            if parent is None:
                raise NoDepartmentException("Parent department does not exist")
            current = parent.parent_id

    def _view(self, department, rows):
        return DepartmentView(
            id=department.id,
            name=department.name,
            description=department.description,
            parent_id=department.parent_id,
            active=department.active,
            child_ids=[row.id for row in rows if row.parent_id == department.id],
        )
