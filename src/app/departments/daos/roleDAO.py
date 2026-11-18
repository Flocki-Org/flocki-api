from fastapi import Depends
from sqlalchemy.orm import joinedload

from src.app.database import SessionLocal, get_db
from src.app.departments.models.database import models
from src.app.groups.models.database.models import Group, GroupMembership


class RoleDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_role(self, role_id):
        return self.db.query(models.AppRole).filter(models.AppRole.id == role_id).first()

    def get_role_by_name(self, name):
        return self.db.query(models.AppRole).filter(models.AppRole.name == name).first()

    def get_ministry_leader_role(self, department_id):
        return (
            self.db.query(models.AppRole)
            .filter(models.AppRole.department_id == department_id, models.AppRole.kind == "ministry_leader")
            .first()
        )

    def get_by_kind(self, kind):
        return self.db.query(models.AppRole).filter(models.AppRole.kind == kind).first()

    def add_role(self, role):
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def save_role(self, role):
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role):
        self.db.delete(role)
        self.db.commit()

    def assignment(self, role_id, person_id, scope_key):
        return (
            self.db.query(models.RoleAssignment)
            .filter(
                models.RoleAssignment.role_id == role_id,
                models.RoleAssignment.person_id == person_id,
                models.RoleAssignment.scope_key == scope_key,
            )
            .first()
        )

    def assignments_for_role(self, role_id):
        return (
            self.db.query(models.RoleAssignment)
            .options(joinedload(models.RoleAssignment.person))
            .filter(models.RoleAssignment.role_id == role_id)
            .all()
        )

    def assignments_for_group(self, group_id):
        return (
            self.db.query(models.RoleAssignment)
            .options(joinedload(models.RoleAssignment.person), joinedload(models.RoleAssignment.role))
            .filter(models.RoleAssignment.group_id == group_id)
            .all()
        )

    def assignments_for_person(self, person_id):
        return (
            self.db.query(models.RoleAssignment)
            .options(joinedload(models.RoleAssignment.role))
            .filter(models.RoleAssignment.person_id == person_id)
            .all()
        )

    def add_assignment(self, assignment):
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete_assignment(self, assignment):
        self.db.delete(assignment)
        self.db.commit()

    def delete_for_group(self, group_id):
        (
            self.db.query(models.RoleAssignment)
            .filter(models.RoleAssignment.group_id == group_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()

    def groups_for_department(self, department_id):
        return (
            self.db.query(Group)
            .filter(Group.department_id == department_id)
            .order_by(Group.name.asc(), Group.id.asc())
            .all()
        )

    def members_for_groups(self, group_ids):
        if not group_ids:
            return []
        return (
            self.db.query(GroupMembership)
            .options(joinedload(GroupMembership.person), joinedload(GroupMembership.role))
            .filter(GroupMembership.group_id.in_(group_ids), GroupMembership.status == "active")
            .all()
        )
