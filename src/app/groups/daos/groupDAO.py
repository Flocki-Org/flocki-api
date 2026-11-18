from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import joinedload, selectinload

from src.app.database import SessionLocal, get_db
from src.app.groups.models.database import models


class GroupDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def _group_options(self, include_members=False):
        options = [joinedload(models.Group.category), joinedload(models.Group.department)]
        if include_members:
            options.append(
                selectinload(models.Group.memberships).selectinload(models.GroupMembership.person)
            )
            options.append(
                selectinload(models.Group.memberships).selectinload(models.GroupMembership.role)
            )
        return options

    def search(self, params, name=None, category_id=None, status=None, include_members=False,
               department_id=None, unassigned=False):
        from fastapi_pagination.ext.sqlalchemy import paginate

        query = self.db.query(models.Group).options(*self._group_options(include_members))
        if name:
            query = query.filter(models.Group.name.ilike(f"%{name}%"))
        if category_id:
            query = query.filter(models.Group.category_id == category_id)
        if status:
            query = query.filter(models.Group.status == status)
        if unassigned:
            query = query.filter(models.Group.department_id.is_(None))
        elif department_id:
            query = query.filter(models.Group.department_id == department_id)
        query = query.order_by(models.Group.name.asc(), models.Group.id.asc())
        return paginate(query, params)

    def get(self, group_id, include_members=False):
        return (
            self.db.query(models.Group)
            .options(*self._group_options(include_members))
            .filter(models.Group.id == group_id)
            .first()
        )

    def add(self, group):
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return self.get(group.id, include_members=True)

    def save(self, group):
        group.updated_at = datetime.now()
        self.db.commit()
        return self.get(group.id, include_members=True)

    def delete(self, group):
        self.db.delete(group)
        self.db.commit()

    def list_categories(self, include_inactive=False):
        query = self.db.query(models.GroupCategory).order_by(models.GroupCategory.name.asc())
        if not include_inactive:
            query = query.filter(models.GroupCategory.active.is_(True))
        return query.all()

    def get_category(self, category_id):
        return self.db.query(models.GroupCategory).filter(models.GroupCategory.id == category_id).first()

    def get_category_by_name(self, name):
        return self.db.query(models.GroupCategory).filter(models.GroupCategory.name == name).first()

    def category_in_use(self, category_id):
        return self.db.query(models.Group).filter(models.Group.category_id == category_id).first() is not None

    def add_category(self, category):
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def save_category(self, category):
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category):
        self.db.delete(category)
        self.db.commit()

    def list_roles(self, include_inactive=False):
        query = self.db.query(models.GroupRole).order_by(models.GroupRole.display_order.asc(), models.GroupRole.name.asc())
        if not include_inactive:
            query = query.filter(models.GroupRole.active.is_(True))
        return query.all()

    def get_role(self, role_id):
        return self.db.query(models.GroupRole).filter(models.GroupRole.id == role_id).first()

    def get_role_by_name(self, name):
        return self.db.query(models.GroupRole).filter(models.GroupRole.name == name).first()

    def add_role(self, role):
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def save_role(self, role):
        self.db.commit()
        self.db.refresh(role)
        return role

    def role_in_use(self, role_id):
        return self.db.query(models.GroupMembership).filter(models.GroupMembership.role_id == role_id).first() is not None

    def delete_role(self, role):
        self.db.delete(role)
        self.db.commit()

    def get_membership(self, group_id, person_id):
        return (
            self.db.query(models.GroupMembership)
            .options(joinedload(models.GroupMembership.role), joinedload(models.GroupMembership.person))
            .filter(
                models.GroupMembership.group_id == group_id,
                models.GroupMembership.person_id == person_id,
            )
            .first()
        )

    def add_membership(self, membership):
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return self.get_membership(membership.group_id, membership.person_id)

    def save_membership(self, membership):
        membership.updated_at = datetime.now()
        self.db.commit()
        return self.get_membership(membership.group_id, membership.person_id)

    def memberships_for_group(self, group_id, include_inactive=False):
        query = (
            self.db.query(models.GroupMembership)
            .options(joinedload(models.GroupMembership.person), joinedload(models.GroupMembership.role))
            .filter(models.GroupMembership.group_id == group_id)
        )
        if not include_inactive:
            query = query.filter(models.GroupMembership.status == "active")
        return query.order_by(models.GroupMembership.id.asc()).all()

    def memberships_for_person(self, person_id):
        return (
            self.db.query(models.GroupMembership)
            .options(
                joinedload(models.GroupMembership.group).joinedload(models.Group.category),
                joinedload(models.GroupMembership.role),
            )
            .filter(models.GroupMembership.person_id == person_id)
            .order_by(models.GroupMembership.id.asc())
            .all()
        )

    def leaders(self, group_id):
        return (
            self.db.query(models.GroupMembership)
            .options(joinedload(models.GroupMembership.person), joinedload(models.GroupMembership.role))
            .join(models.GroupRole)
            .filter(
                models.GroupMembership.group_id == group_id,
                models.GroupMembership.status == "active",
                models.GroupRole.is_leader.is_(True),
            )
            .all()
        )

    def add_image(self, group, image):
        self.db.add(models.GroupImage(group=group, image=image, created=datetime.now()))
        self.db.commit()
