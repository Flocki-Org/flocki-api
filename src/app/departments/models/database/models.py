from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.app.database import Base
from src.app.people.models.database.models import Person  # noqa: F401


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("departments.id"))
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    parent = relationship("Department", remote_side=[id], backref="children")
    __table_args__ = (
        Index("ix_departments_parent", "parent_id"),
        Index("ix_departments_name", "name"),
    )


class DepartmentPerson(Base):
    __tablename__ = "department_people"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    department = relationship("Department")
    person = relationship("Person")
    __table_args__ = (
        Index("ux_department_person", "department_id", "person_id", unique=True),
        Index("ix_department_person_person", "person_id"),
    )


class DepartmentGroup(Base):
    __tablename__ = "department_groups"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    department = relationship("Department")
    __table_args__ = (
        Index("ux_department_group", "department_id", "group_id", unique=True),
        Index("ix_department_group_group", "group_id"),
    )


class AppRole(Base):
    """A named role. Permissions will attach here later. A ministry leader role belongs to one ministry."""

    __tablename__ = "app_roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    kind = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    department = relationship("Department")
    __table_args__ = (
        Index("ux_app_roles_name", "name", unique=True),
        Index("ix_app_roles_department", "department_id"),
        Index("ix_app_roles_kind", "kind"),
    )


class RoleAssignment(Base):
    """A person holds a role. group_id is set when the role is scoped to one group."""

    __tablename__ = "role_assignments"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("app_roles.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    scope_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    role = relationship("AppRole")
    person = relationship("Person")
    __table_args__ = (
        Index("ux_role_assignment_scope", "role_id", "person_id", "scope_key", unique=True),
        Index("ix_role_assignment_person", "person_id"),
        Index("ix_role_assignment_group", "group_id"),
    )
