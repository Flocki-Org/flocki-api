import datetime

import pytest
from fastapi_pagination import Params
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.audit.daos.auditDAO import AuditDAO, ImportDAO
from src.app.customfields.daos.customFieldDAO import CustomFieldDAO
from src.app.customfields.models.fields import CreateCustomField, CustomFieldOptionInput, CustomFieldValueInput
from src.app.customfields.services.customFieldService import CustomFieldService
from src.app.customfields.validation import CustomFieldValidationError, normalise_custom_value
from src.app.database import Base
from src.app.departments.daos.departmentDAO import DepartmentDAO
from src.app.departments.daos.roleDAO import RoleDAO
from src.app.departments.services.departmentService import (
    DepartmentCycleException,
    DepartmentGroupInput,
    DepartmentInput,
    DepartmentPersonInput,
    DepartmentService,
    DepartmentUpdate,
)
from src.app.groups.daos.groupDAO import GroupDAO
from src.app.groups.services.groupService import (
    AddGroupMember,
    CreateGroup,
    DuplicateMembershipException,
    GroupCategoryInput,
    GroupInUseException,
    GroupService,
)
from src.app.imports.models.bundle import ImportBundle, ImportPerson
from src.app.imports.services.importService import ImportService
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.model_registry import import_all_models
from src.app.people.daos.addressDAO import AddressDAO
from src.app.people.daos.categoryDAO import CategoryDAO
from src.app.people.daos.householdDAO import HouseholdDAO
from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.addressFactory import AddressFactory
from src.app.people.factories.householdFactory import HouseholdFactory
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.contacts import CategoryInput, PersonEmailInput, PersonPhoneInput, EmergencyContactInput
from src.app.people.models.database.models import Address, Person
from src.app.people.models.household import CreateHousehold
from src.app.people.models.people import CreatePerson, UpdatePerson
from src.app.people.models.search import PeopleSearchFilters
from src.app.people.services.categoryService import CategoryService
from src.app.people.services.householdService import (
    HouseholdService,
    LeaderMustBeMemberOfHouseholdException,
    UnableToRemoveLeaderFromHouseholdException,
)
from src.app.people.services.householdUtils import HouseholdUtils
from src.app.people.services.peopleService import DuplicateRelationshipException, PeopleService


@pytest.fixture()
def services():
    import_all_models()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    people_factory = PeopleFactory(address_factory=AddressFactory(), media_factory=MediaFactory())
    household_factory = HouseholdFactory(people_factory=people_factory, media_factory=MediaFactory())
    people_dao = PeopleDAO(db)
    address_dao = AddressDAO(db)
    household_dao = HouseholdDAO(db)
    category_dao = CategoryDAO(db)
    custom_fields = CustomFieldService(dao=CustomFieldDAO(db))
    people = PeopleService(
        peopleDAO=people_dao,
        addressDAO=address_dao,
        people_factory=people_factory,
        household_DAO=household_dao,
        household_utils=HouseholdUtils(),
        category_dao=category_dao,
        custom_field_service=custom_fields,
        audit_dao=AuditDAO(db),
    )
    households = HouseholdService(
        household_DAO=household_dao,
        household_factory=household_factory,
        peopleDAO=people_dao,
        people_factory=people_factory,
        address_DAO=address_dao,
        household_utils=HouseholdUtils(),
        media_factory=MediaFactory(),
    )
    role_dao = RoleDAO(db)
    department_dao = DepartmentDAO(db)
    group_dao = GroupDAO(db)
    groups = GroupService(
        group_dao=group_dao,
        people_dao=people_dao,
        people_factory=people_factory,
        address_dao=address_dao,
        role_dao=role_dao,
        department_dao=department_dao,
    )
    departments = DepartmentService(
        department_dao=department_dao,
        people_dao=people_dao,
        group_dao=group_dao,
        role_dao=role_dao,
    )
    importer = ImportService(
        db=db,
        import_dao=ImportDAO(db),
        people_factory=people_factory,
        custom_field_service=custom_fields,
        group_service=groups,
    )
    yield {
        "db": db,
        "people": people,
        "households": households,
        "groups": groups,
        "departments": departments,
        "categories": CategoryService(category_dao=category_dao),
        "fields": custom_fields,
        "importer": importer,
    }
    db.close()


def test_custom_field_types_are_validated():
    assert normalise_custom_value("text", "hello")["value_text"] == "hello"
    assert normalise_custom_value("long_text", "a" * 2000)["value_text"].startswith("a")
    assert normalise_custom_value("number", "12")["value_number"] == 12
    assert normalise_custom_value("decimal", "1.5")["value_decimal"] == pytest.approx(1.5)
    assert normalise_custom_value("date", "2020-01-02")["value_date"] == datetime.date(2020, 1, 2)
    assert normalise_custom_value("boolean", "yes")["value_bool"] is True
    assert normalise_custom_value("single_select", "S", ["S", "M"])["value_text"] == "S"
    assert normalise_custom_value("multi_select", ["S", "M"], ["S", "M"])["value_json"] == ["S", "M"]
    assert normalise_custom_value("url", "https://example.com")["value_text"] == "https://example.com"
    assert normalise_custom_value("email", "person@example.com")["value_text"] == "person@example.com"
    assert normalise_custom_value("phone", "+27111222333")["value_text"] == "+27111222333"
    with pytest.raises(CustomFieldValidationError):
        normalise_custom_value("single_select", "XL", ["S"])
    with pytest.raises(CustomFieldValidationError):
        normalise_custom_value("email", "not-an-email")
    with pytest.raises(CustomFieldValidationError):
        normalise_custom_value("boolean", "", required=True)


def test_minimal_and_full_person_partial_update_archive_and_search(services):
    people = services["people"]
    minimal = people.create_person(CreatePerson(preferred_name="Sam"))
    assert minimal.preferred_name == "Sam"
    assert minimal.first_name is None

    category = services["categories"].create(CategoryInput(name="Volunteers", colour="#112233"))
    field = services["fields"].create(CreateCustomField(
        name="Shirt size",
        field_type="single_select",
        options=[CustomFieldOptionInput(value="S"), CustomFieldOptionInput(value="M")],
    ))
    full = people.create_person(CreatePerson(
        first_name="Ada",
        preferred_name="A",
        middle_name="Augusta",
        last_name="Lovelace",
        title="Ms",
        gender="female",
        marital_status="married",
        date_of_birth=datetime.date(1990, 12, 10),
        marriage_date=datetime.date(2015, 6, 1),
        biography="Mathematician",
        lifecycle_status="member",
        membership_status="member",
        occupation="Engineer",
        emails=[PersonEmailInput(email="ada@example.com", is_primary=True)],
        phones=[PersonPhoneInput(number="0820000000", phone_type="mobile", is_primary=True)],
        emergency_contacts=[EmergencyContactInput(name="Charles", phone="0830000000")],
        category_ids=[category.id],
        custom_fields=[CustomFieldValueInput(field_id=field.id, value="M")],
    ))
    assert full.email == "ada@example.com"
    assert full.categories[0].name == "Volunteers"
    assert full.custom_fields[0].value == "M"
    assert len(full.phones) == 1

    updated = people.update_person(full.id, UpdatePerson(id=full.id, occupation="Analyst"))
    assert updated.occupation == "Analyst"
    assert updated.email == "ada@example.com"
    assert updated.last_name == "Lovelace"

    archived = people.archive_person(full.id, reason="moved")
    assert archived.lifecycle_status == "archived"
    assert archived.archived_at is not None
    restored = people.restore_person(full.id)
    assert restored.lifecycle_status == "member"
    assert restored.archived_at is None

    page = people.get_all(Params(page=1, size=10), PeopleSearchFilters(last_name="Love", category_ids=[category.id]))
    assert [person.id for person in page.items] == [full.id]
    birthdays = people.report("birthdays", days=370)
    assert full.id in [person.id for person in birthdays]


def test_household_leader_members_and_relationships(services):
    people = services["people"]
    households = services["households"]
    db = services["db"]
    leader = people.create_person(CreatePerson(first_name="Alex", last_name="Ng"))
    spouse = people.create_person(CreatePerson(first_name="Blake", last_name="Ng"))
    child = people.create_person(CreatePerson(first_name="Casey", last_name="Ng"))
    address = Address(type="home", street_number="1", street="Main", suburb="Town", city="City", postal_code="0001")
    db.add(address)
    db.commit()

    household = households.add_household(CreateHousehold(
        leader_id=leader.id,
        people_ids=[leader.id],
        address_id=address.id,
        name="Ng household",
        notes="Corner house",
    ))
    assert household.name == "Ng household"
    assert household.leader.id == leader.id

    households.add_member(household.id, spouse.id)
    with pytest.raises(LeaderMustBeMemberOfHouseholdException):
        households.set_leader(household.id, child.id)
    households.set_leader(household.id, spouse.id)
    with pytest.raises(UnableToRemoveLeaderFromHouseholdException):
        households.remove_member(household.id, spouse.id)
    households.remove_member(household.id, leader.id)

    people.add_relationship(leader.id, spouse.id, "spouse")
    outgoing = people.relationships(leader.id)
    incoming = people.relationships(spouse.id)
    assert outgoing[0].relationship_type == "spouse"
    assert incoming[0].relationship_type == "spouse"
    assert incoming[0].direction == "incoming"
    with pytest.raises(DuplicateRelationshipException):
        people.add_relationship(spouse.id, leader.id, "spouse")
    with pytest.raises(DuplicateRelationshipException):
        people.add_relationship(leader.id, leader.id, "sibling")


def test_groups_membership_roles_archive_and_departments(services):
    people = services["people"]
    groups = services["groups"]
    departments = services["departments"]
    person = people.create_person(CreatePerson(first_name="Drew", last_name="Pillay"))
    other = people.create_person(CreatePerson(first_name="Erin", last_name="Pillay"))
    category = groups.create_category(GroupCategoryInput(name="Bible study", colour="#336699"))
    group = groups.create(CreateGroup(
        name="Tuesday study",
        category_id=category.id,
        leader_person_id=person.id,
    ))
    assert group.leaders[0].person.id == person.id
    groups.add_member(group.id, AddGroupMember(person_id=other.id, role_name="Member"))
    with pytest.raises(DuplicateMembershipException):
        groups.add_member(group.id, AddGroupMember(person_id=other.id, role_name="Member"))
    person_groups = groups.groups_for_person(person.id)
    assert person_groups[0]["group_name"] == "Tuesday study"
    assert person_groups[0]["role"] == "Leader"
    with pytest.raises(GroupInUseException):
        groups.delete(group.id)
    archived = groups.archive(group.id)
    assert archived.status == "archived"
    restored = groups.restore(group.id)
    assert restored.status == "active"

    parent = departments.create(DepartmentInput(name="Children's Ministry"))
    child = departments.create(DepartmentInput(name="Sunday School", parent_id=parent.id))
    departments.add_person(child.id, DepartmentPersonInput(person_id=person.id))
    with pytest.raises(DepartmentCycleException):
        departments.update(parent.id, DepartmentUpdate(parent_id=child.id))


def test_ministry_leader_role_is_separate_from_group_membership(services):
    people = services["people"]
    groups = services["groups"]
    departments = services["departments"]
    jane = people.create_person(CreatePerson(first_name="Jane", last_name="Leader"))
    ministry = departments.create(DepartmentInput(
        name="Worship Ministry",
        leader_person_id=jane.id,
        group_names=["Band"],
    ))
    assert ministry.leader_role.name == "Worship Ministry Leader"
    assert ministry.leaders[0].person_id == jane.id
    assert [group.name for group in ministry.groups] == ["Band"]

    departments.update(ministry.id, DepartmentUpdate(name="Worship"))
    renamed_ministry = departments.rename_leader_role(ministry.id, "Worship Lead")
    assert renamed_ministry.name == "Worship"
    assert renamed_ministry.leader_role.name == "Worship Lead"

    loose = groups.create(CreateGroup(name="Unassigned team"))
    assert loose.ministry is None
    assigned = departments.add_group(ministry.id, DepartmentGroupInput(group_id=loose.id))
    assert {group.name for group in assigned.groups} == {"Band", "Unassigned team"}
    assert groups.members(loose.id) == []

    groups.add_administrator(loose.id, jane.id)
    assert groups.members(loose.id) == []
    band = next(group for group in departments.get(ministry.id).groups if group.name == "Band")
    assert band.members == []
    assigned_group = next(group for group in departments.get(ministry.id).groups if group.name == "Unassigned team")
    assert assigned_group.members == []
    groups.add_member(loose.id, AddGroupMember(person_id=jane.id, role_name="Member"))
    with_member = next(group for group in departments.get(ministry.id).groups if group.name == "Unassigned team")
    assert with_member.members[0].person_id == jane.id
    assert with_member.members[0].role == "Member"
    assert groups.administrators(loose.id)[0].person.id == jane.id
    involvement = departments.ministries_for_person(jane.id)
    assert involvement.ministries[0].role_name == "Worship Lead"
    assert involvement.group_administrations[0].group_name == "Unassigned team"


def test_import_is_idempotent(services):
    importer = services["importer"]
    db = services["db"]
    bundle = ImportBundle(people=[
        ImportPerson(external_id="elv-1", first_name="Ada", last_name="Lovelace", email="ada@example.com", unknown_note="keep me"),
    ])
    first = importer.import_bundle(bundle)
    second = importer.import_bundle(bundle)
    assert first["people"]["created"] == 1
    assert second["people"]["updated"] == 1
    assert second["people"]["created"] == 0
    assert db.query(Person).count() == 1
