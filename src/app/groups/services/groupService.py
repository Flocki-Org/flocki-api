import datetime
from typing import Optional

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field

from src.app.groups.daos.groupDAO import GroupDAO
from src.app.groups.models.database import models
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import BasicViewPerson, ViewAddress
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.peopleService import NoPersonException


class DuplicateMembershipException(Exception):
    pass


class NoGroupException(Exception):
    pass


class NoGroupRoleException(Exception):
    pass


class GroupInUseException(Exception):
    pass


class GroupCategoryInput(BaseModel):
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    active: bool = True

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Small groups", "colour": "#3D7A4A"}})


class GroupCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    colour: Optional[str] = None
    active: Optional[bool] = None


class GroupCategoryView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    active: bool = True


class GroupRoleInput(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True
    is_leader: bool = False
    display_order: int = 0


class GroupRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    is_leader: Optional[bool] = None
    display_order: Optional[int] = None


class GroupRoleView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    active: bool = True
    is_leader: bool = False
    display_order: int = 0


class CreateGroup(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    status: str = "active"
    meeting_location: Optional[str] = None
    meeting_address_id: Optional[int] = None
    meeting_day: Optional[str] = None
    meeting_start_time: Optional[datetime.time] = None
    meeting_end_time: Optional[datetime.time] = None
    meeting_frequency: Optional[str] = None
    meeting_notes: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    leader_person_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tuesday Bible study",
                "category_id": 1,
                "meeting_day": "Tuesday",
                "meeting_frequency": "weekly",
                "meeting_start_time": "19:00:00",
                "leader_person_id": 1,
            }
        }
    )


class UpdateGroup(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    meeting_location: Optional[str] = None
    meeting_address_id: Optional[int] = None
    meeting_day: Optional[str] = None
    meeting_start_time: Optional[datetime.time] = None
    meeting_end_time: Optional[datetime.time] = None
    meeting_frequency: Optional[str] = None
    meeting_notes: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class AddGroupMember(BaseModel):
    person_id: int
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    status: str = "active"
    date_joined: Optional[datetime.date] = None
    notes: Optional[str] = None


class UpdateGroupMember(BaseModel):
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    status: Optional[str] = None
    date_joined: Optional[datetime.date] = None
    date_left: Optional[datetime.date] = None
    notes: Optional[str] = None


class GroupMemberView(BaseModel):
    person: BasicViewPerson
    role: Optional[GroupRoleView] = None
    status: str
    date_joined: Optional[datetime.date] = None
    date_left: Optional[datetime.date] = None
    notes: Optional[str] = None


class GroupView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[GroupCategoryView] = None
    status: str
    meeting_location: Optional[str] = None
    meeting_address: Optional[ViewAddress] = None
    meeting_day: Optional[str] = None
    meeting_start_time: Optional[datetime.time] = None
    meeting_end_time: Optional[datetime.time] = None
    meeting_frequency: Optional[str] = None
    meeting_notes: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    archived_at: Optional[datetime.datetime] = None
    members: Optional[list[GroupMemberView]] = None
    leaders: list[GroupMemberView] = Field(default_factory=list)


GROUP_COLUMNS = (
    "name",
    "description",
    "category_id",
    "status",
    "meeting_location",
    "meeting_address_id",
    "meeting_day",
    "meeting_start_time",
    "meeting_end_time",
    "meeting_frequency",
    "meeting_notes",
    "contact_email",
    "contact_phone",
)


class GroupService:
    def __init__(self, group_dao: GroupDAO = Depends(GroupDAO), people_dao: PeopleDAO = Depends(PeopleDAO),
                 people_factory: PeopleFactory = Depends(PeopleFactory), address_dao: AddressDAO = Depends(AddressDAO)):
        self.group_dao = group_dao
        self.people_dao = people_dao
        self.people_factory = people_factory
        self.address_dao = address_dao

    def search(self, params, name=None, category_id=None, status=None, include_members=False):
        page = self.group_dao.search(params, name, category_id, status, include_members)
        return page.__class__.create(
            items=[self.to_view(group, include_members=include_members) for group in page.items],
            params=params,
            total=page.total,
        )

    def get(self, group_id, include_members=False):
        group = self.group_dao.get(group_id, include_members=include_members)
        if group is None:
            raise NoGroupException("Group does not exist")
        return self.to_view(group, include_members=include_members)

    def create(self, payload: CreateGroup):
        self._require_category(payload.category_id)
        self._require_address(payload.meeting_address_id)
        data = payload.model_dump(exclude={"leader_person_id"})
        group = models.Group(**data)
        created = self.group_dao.add(group)
        if payload.leader_person_id:
            self.add_member(created.id, AddGroupMember(person_id=payload.leader_person_id, role_name="Leader"))
            created = self.group_dao.get(created.id, include_members=True)
        return self.to_view(created, include_members=True)

    def update(self, group_id, payload: UpdateGroup):
        group = self._require_group(group_id)
        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data:
            self._require_category(data["category_id"])
        if "meeting_address_id" in data:
            self._require_address(data["meeting_address_id"])
        for key, value in data.items():
            if key in GROUP_COLUMNS:
                setattr(group, key, value)
        if data.get("status") == "archived":
            group.archived_at = datetime.datetime.now()
        elif "status" in data and data["status"] != "archived":
            group.archived_at = None
        return self.to_view(self.group_dao.save(group), include_members=True)

    def archive(self, group_id):
        group = self._require_group(group_id)
        group.status = "archived"
        group.archived_at = datetime.datetime.now()
        return self.to_view(self.group_dao.save(group), include_members=False)

    def restore(self, group_id):
        group = self._require_group(group_id)
        group.status = "active"
        group.archived_at = None
        return self.to_view(self.group_dao.save(group), include_members=False)

    def delete(self, group_id, force=False):
        group = self._require_group(group_id)
        memberships = self.group_dao.memberships_for_group(group_id, include_inactive=True)
        if memberships and not force:
            raise GroupInUseException("Remove members or archive the group before deleting it")
        self.group_dao.delete(group)

    def add_member(self, group_id, payload: AddGroupMember):
        self._require_group(group_id)
        person = self.people_dao.get_person_by_id(payload.person_id)
        if person is None:
            raise NoPersonException(f"No person with the following ID: {payload.person_id}")
        role = self._resolve_role(payload.role_id, payload.role_name or "Member")
        existing = self.group_dao.get_membership(group_id, payload.person_id)
        if existing and existing.status == "active":
            raise DuplicateMembershipException("That person is already an active member of this group")
        if existing:
            existing.status = payload.status or "active"
            existing.role_id = role.id
            existing.date_joined = payload.date_joined or existing.date_joined or datetime.date.today()
            existing.date_left = None
            existing.notes = payload.notes if payload.notes is not None else existing.notes
            return self._member(self.group_dao.save_membership(existing))
        membership = models.GroupMembership(
            group_id=group_id,
            person_id=payload.person_id,
            role_id=role.id,
            status=payload.status or "active",
            date_joined=payload.date_joined or datetime.date.today(),
            notes=payload.notes,
        )
        return self._member(self.group_dao.add_membership(membership))

    def update_member(self, group_id, person_id, payload: UpdateGroupMember):
        membership = self.group_dao.get_membership(group_id, person_id)
        if membership is None:
            raise NoPersonException("That person is not a member of this group")
        data = payload.model_dump(exclude_unset=True)
        if "role_id" in data or "role_name" in data:
            role = self._resolve_role(data.pop("role_id", None), data.pop("role_name", None))
            membership.role_id = role.id
        else:
            data.pop("role_id", None)
            data.pop("role_name", None)
        for key, value in data.items():
            setattr(membership, key, value)
        return self._member(self.group_dao.save_membership(membership))

    def remove_member(self, group_id, person_id):
        membership = self.group_dao.get_membership(group_id, person_id)
        if membership is None:
            raise NoPersonException("That person is not a member of this group")
        membership.status = "inactive"
        membership.date_left = datetime.date.today()
        return self._member(self.group_dao.save_membership(membership))

    def members(self, group_id, include_inactive=False):
        self._require_group(group_id)
        return [self._member(row) for row in self.group_dao.memberships_for_group(group_id, include_inactive)]

    def leaders(self, group_id):
        self._require_group(group_id)
        return [self._member(row) for row in self.group_dao.leaders(group_id)]

    def groups_for_person(self, person_id):
        if self.people_dao.get_person_by_id(person_id) is None:
            raise NoPersonException(f"No person with the following ID: {person_id}")
        results = []
        for membership in self.group_dao.memberships_for_person(person_id):
            results.append({
                "group_id": membership.group_id,
                "group_name": membership.group.name,
                "role": membership.role.name if membership.role else None,
                "status": membership.status,
                "category": membership.group.category.name if membership.group.category else None,
            })
        return results

    def create_category(self, payload: GroupCategoryInput):
        if self.group_dao.get_category_by_name(payload.name):
            raise GroupInUseException("A group category with that name already exists")
        return self._category(self.group_dao.add_category(models.GroupCategory(**payload.model_dump())))

    def update_category(self, category_id, payload: GroupCategoryUpdate):
        category = self.group_dao.get_category(category_id)
        if category is None:
            raise NoGroupException("Group category does not exist")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        return self._category(self.group_dao.save_category(category))

    def delete_category(self, category_id):
        category = self.group_dao.get_category(category_id)
        if category is None:
            raise NoGroupException("Group category does not exist")
        if self.group_dao.category_in_use(category_id):
            raise GroupInUseException("Deactivate this category while groups still use it")
        self.group_dao.delete_category(category)

    def list_categories(self, include_inactive=False):
        return [self._category(row) for row in self.group_dao.list_categories(include_inactive)]

    def create_role(self, payload: GroupRoleInput):
        if self.group_dao.get_role_by_name(payload.name):
            raise GroupInUseException("A group role with that name already exists")
        return self._role(self.group_dao.add_role(models.GroupRole(**payload.model_dump())))

    def update_role(self, role_id, payload: GroupRoleUpdate):
        role = self.group_dao.get_role(role_id)
        if role is None:
            raise NoGroupRoleException("Group role does not exist")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(role, key, value)
        return self._role(self.group_dao.save_role(role))

    def delete_role(self, role_id):
        role = self.group_dao.get_role(role_id)
        if role is None:
            raise NoGroupRoleException("Group role does not exist")
        if self.group_dao.role_in_use(role_id):
            role.active = False
            return self._role(self.group_dao.save_role(role))
        self.group_dao.delete_role(role)
        return None

    def list_roles(self, include_inactive=False):
        return [self._role(row) for row in self.group_dao.list_roles(include_inactive)]

    def to_view(self, group, include_members=False):
        members = None
        leaders = []
        loaded_members = group.memberships if include_members else []
        if include_members:
            members = [self._member(row) for row in loaded_members if row.status == "active"]
            leaders = [member for member in members if member.role and member.role.is_leader]
        address = None
        if group.meeting_address is not None:
            address = ViewAddress(
                id=group.meeting_address.id,
                type=group.meeting_address.type,
                building=group.meeting_address.building,
                unit=group.meeting_address.unit,
                street_number=group.meeting_address.street_number,
                street=group.meeting_address.street,
                suburb=group.meeting_address.suburb,
                city=group.meeting_address.city,
                province=group.meeting_address.province,
                country=group.meeting_address.country,
                postal_code=group.meeting_address.postal_code,
                latitude=group.meeting_address.latitude,
                longitude=group.meeting_address.longitude,
            )
        return GroupView(
            id=group.id,
            name=group.name,
            description=group.description,
            category=self._category(group.category) if group.category else None,
            status=group.status,
            meeting_location=group.meeting_location,
            meeting_address=address,
            meeting_day=group.meeting_day,
            meeting_start_time=group.meeting_start_time,
            meeting_end_time=group.meeting_end_time,
            meeting_frequency=group.meeting_frequency,
            meeting_notes=group.meeting_notes,
            contact_email=group.contact_email,
            contact_phone=group.contact_phone,
            created_at=group.created_at,
            updated_at=group.updated_at,
            archived_at=group.archived_at,
            members=members,
            leaders=leaders,
        )

    def _member(self, membership):
        person = membership.person
        return GroupMemberView(
            person=self.people_factory.create_basic_person_view_from_person_entity(person) if person else BasicViewPerson(id=membership.person_id),
            role=self._role(membership.role) if membership.role else None,
            status=membership.status,
            date_joined=membership.date_joined,
            date_left=membership.date_left,
            notes=membership.notes,
        )

    def _category(self, category):
        return GroupCategoryView(
            id=category.id,
            name=category.name,
            description=category.description,
            colour=category.colour,
            active=category.active,
        )

    def _role(self, role):
        return GroupRoleView(
            id=role.id,
            name=role.name,
            description=role.description,
            active=role.active,
            is_leader=role.is_leader,
            display_order=role.display_order,
        )

    def _resolve_role(self, role_id, role_name):
        if role_id:
            role = self.group_dao.get_role(role_id)
            if role is None:
                raise NoGroupRoleException("Group role does not exist")
            return role
        name = role_name or "Member"
        role = self.group_dao.get_role_by_name(name)
        if role is None:
            role = self.group_dao.add_role(models.GroupRole(name=name, is_leader=name == "Leader", active=True))
        return role

    def _require_group(self, group_id):
        group = self.group_dao.get(group_id)
        if group is None:
            raise NoGroupException("Group does not exist")
        return group

    def _require_category(self, category_id):
        if category_id is None:
            return
        if self.group_dao.get_category(category_id) is None:
            raise NoGroupException("Group category does not exist")

    def _require_address(self, address_id):
        if address_id is None or not hasattr(self.address_dao, "get_address_by_id"):
            return
        if self.address_dao.get_address_by_id(address_id) is None:
            raise NoAddressException(f"No address with the following ID: {address_id}")
