from typing import Optional

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field

from src.app.departments.daos.departmentDAO import DepartmentDAO
from src.app.departments.daos.roleDAO import RoleDAO
from src.app.departments.models.database import models
from src.app.groups.daos.groupDAO import GroupDAO
from src.app.groups.models.database.models import Group
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
    leader_person_id: Optional[int] = None
    group_names: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Worship Ministry", "leader_person_id": 1, "group_names": ["Band"]}}
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
    group_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class RenameRoleInput(BaseModel):
    name: str


class MinistryRoleView(BaseModel):
    id: int
    name: str


class MinistryPersonView(BaseModel):
    person_id: int
    first_name: str
    last_name: str


class MinistryGroupMemberView(BaseModel):
    person_id: int
    first_name: str
    last_name: str
    role: Optional[str] = None


class MinistryGroupView(BaseModel):
    id: int
    name: str
    status: str
    member_count: int = 0
    members: list[MinistryGroupMemberView] = Field(default_factory=list)


class DepartmentView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    active: bool = True
    child_ids: list[int] = []
    leader_role: Optional[MinistryRoleView] = None
    leaders: list[MinistryPersonView] = Field(default_factory=list)
    groups: list[MinistryGroupView] = Field(default_factory=list)
    group_count: int = 0


class PersonMinistryLink(BaseModel):
    department_id: int
    name: str
    role_name: str


class PersonGroupAdminLink(BaseModel):
    group_id: int
    group_name: str
    role_name: str


class PersonMinistryInvolvement(BaseModel):
    ministries: list[PersonMinistryLink] = Field(default_factory=list)
    group_administrations: list[PersonGroupAdminLink] = Field(default_factory=list)


class DepartmentService:
    def __init__(self, department_dao: DepartmentDAO = Depends(DepartmentDAO),
                 people_dao: PeopleDAO = Depends(PeopleDAO), group_dao: GroupDAO = Depends(GroupDAO),
                 role_dao: RoleDAO = Depends(RoleDAO)):
        self.department_dao = department_dao
        self.people_dao = people_dao
        self.group_dao = group_dao
        self.role_dao = role_dao

    def list_departments(self, include_inactive=False):
        rows = self.department_dao.list_departments(include_inactive)
        return [self._view(row, rows) for row in rows]

    def get(self, department_id):
        department = self._require(department_id)
        return self._view(department, self.department_dao.list_departments(include_inactive=True))

    def create(self, payload: DepartmentInput):
        self._validate_parent(None, payload.parent_id)
        if payload.leader_person_id and self.people_dao.get_person_by_id(payload.leader_person_id) is None:
            raise NoPersonException(f"No person with the following ID: {payload.leader_person_id}")
        department = models.Department(
            name=payload.name.strip(),
            description=payload.description,
            parent_id=payload.parent_id,
            active=payload.active,
        )
        created = self.department_dao.add(department)
        if payload.leader_person_id:
            self._grant_leader(created, payload.leader_person_id)
        for raw_name in payload.group_names:
            name = (raw_name or "").strip()
            if name:
                self.group_dao.add(Group(
                    name=name,
                    status="active",
                    department_id=created.id,
                ))
        return self.get(created.id)

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
            raise DepartmentInUseException("Remove people and groups from this ministry first")
        if self.role_dao.groups_for_department(department_id):
            raise DepartmentInUseException("Remove groups from this ministry first")
        role = self.role_dao.get_ministry_leader_role(department_id)
        if role and self.role_dao.assignments_for_role(role.id):
            raise DepartmentInUseException("Remove ministry leaders first")
        if role:
            self.role_dao.delete_role(role)
        self.department_dao.delete(department)

    def add_leader(self, department_id, payload: DepartmentPersonInput):
        department = self._require(department_id)
        if self.people_dao.get_person_by_id(payload.person_id) is None:
            raise NoPersonException(f"No person with the following ID: {payload.person_id}")
        self._grant_leader(department, payload.person_id)
        return self.get(department_id)

    def remove_leader(self, department_id, person_id):
        self._require(department_id)
        role = self.role_dao.get_ministry_leader_role(department_id)
        link = self.role_dao.assignment(role.id, person_id, "ministry") if role else None
        if link is None:
            raise NoPersonException("That person is not a leader of this ministry")
        self.role_dao.delete_assignment(link)
        return self.get(department_id)

    def rename_leader_role(self, department_id, name):
        self._require(department_id)
        role = self.role_dao.get_ministry_leader_role(department_id)
        if role is None:
            raise NoDepartmentException("This ministry has no leader role yet")
        role.name = self._unique_role_name(name, ignore_id=role.id)
        self.role_dao.save_role(role)
        return self.get(department_id)

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
        name = (payload.name or "").strip()
        if name:
            self.group_dao.add(Group(
                name=name,
                description=payload.description,
                status="active",
                department_id=department_id,
            ))
            return self.get(department_id)
        if payload.group_id is None:
            raise DepartmentInUseException("Choose a group or give the new group a name")
        group = self.group_dao.get(payload.group_id)
        if group is None:
            raise NoDepartmentException("Group does not exist")
        if group.department_id and group.department_id != department_id:
            raise DepartmentInUseException("That group already belongs to another ministry")
        group.department_id = department_id
        self.group_dao.save(group)
        return self.get(department_id)

    def remove_group(self, department_id, group_id):
        self._require(department_id)
        group = self.group_dao.get(group_id)
        link = self.department_dao.group_link(department_id, group_id)
        if (group is None or group.department_id != department_id) and link is None:
            raise NoDepartmentException("That group is not in this ministry")
        if group is not None and group.department_id == department_id:
            group.department_id = None
            self.group_dao.save(group)
        if link is not None:
            self.department_dao.delete_group(link)
        return self.get(department_id)

    def ministries_for_person(self, person_id):
        if self.people_dao.get_person_by_id(person_id) is None:
            raise NoPersonException(f"No person with the following ID: {person_id}")
        ministries = []
        administrations = []
        for assignment in self.role_dao.assignments_for_person(person_id):
            role = assignment.role
            if role is None:
                continue
            if role.kind == "ministry_leader" and role.department_id:
                department = self.department_dao.get(role.department_id)
                if department is not None:
                    ministries.append(PersonMinistryLink(
                        department_id=department.id,
                        name=department.name,
                        role_name=role.name,
                    ))
            elif role.kind == "group_administrator" and assignment.group_id:
                group = self.group_dao.get(assignment.group_id)
                if group is not None:
                    administrations.append(PersonGroupAdminLink(
                        group_id=group.id,
                        group_name=group.name,
                        role_name=role.name,
                    ))
        return PersonMinistryInvolvement(ministries=ministries, group_administrations=administrations)

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

    def _grant_leader(self, department, person_id):
        role = self._ensure_leader_role(department)
        if self.role_dao.assignment(role.id, person_id, "ministry"):
            raise DepartmentInUseException("That person already holds this ministry's leader role")
        self.role_dao.add_assignment(models.RoleAssignment(
            role_id=role.id,
            person_id=person_id,
            scope_key="ministry",
        ))

    def _ensure_leader_role(self, department):
        existing = self.role_dao.get_ministry_leader_role(department.id)
        if existing is not None:
            return existing
        role = models.AppRole(
            name=self._unique_role_name(f"{department.name.strip()} Leader"),
            kind="ministry_leader",
            department_id=department.id,
        )
        return self.role_dao.add_role(role)

    def _unique_role_name(self, name, ignore_id=None):
        cleaned = (name or "").strip()
        if not cleaned:
            raise DepartmentInUseException("A role needs a name")
        other = self.role_dao.get_role_by_name(cleaned)
        if other is not None and other.id != ignore_id:
            raise DepartmentInUseException("A role with that name already exists")
        return cleaned

    def _view(self, department, rows):
        role = self.role_dao.get_ministry_leader_role(department.id)
        leaders = []
        if role is not None:
            for assignment in self.role_dao.assignments_for_role(role.id):
                person = assignment.person
                if person is None:
                    continue
                leaders.append(MinistryPersonView(
                    person_id=person.id,
                    first_name=person.first_name or "",
                    last_name=person.last_name or "",
                ))
        groups = self.role_dao.groups_for_department(department.id)
        members_by_group: dict[int, list[MinistryGroupMemberView]] = {}
        for membership in self.role_dao.members_for_groups([group.id for group in groups]):
            person = membership.person
            if person is None:
                continue
            members_by_group.setdefault(membership.group_id, []).append(MinistryGroupMemberView(
                person_id=person.id,
                first_name=person.first_name or "",
                last_name=person.last_name or "",
                role=membership.role.name if membership.role else None,
            ))
        for people in members_by_group.values():
            people.sort(key=lambda member: (member.last_name.lower(), member.first_name.lower()))
        return DepartmentView(
            id=department.id,
            name=department.name,
            description=department.description,
            parent_id=department.parent_id,
            active=department.active,
            child_ids=[row.id for row in rows if row.parent_id == department.id],
            leader_role=MinistryRoleView(id=role.id, name=role.name) if role else None,
            leaders=leaders,
            groups=[
                MinistryGroupView(
                    id=group.id,
                    name=group.name,
                    status=group.status,
                    member_count=len(members_by_group.get(group.id, [])),
                    members=members_by_group.get(group.id, []),
                )
                for group in groups
            ],
            group_count=len(groups),
        )
