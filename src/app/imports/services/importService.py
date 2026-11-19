import datetime

from fastapi import Depends

from src.app.audit.daos.auditDAO import ImportDAO
from src.app.customfields.models.database.models import CustomFieldDefinition, CustomFieldOption
from src.app.customfields.models.fields import CustomFieldValueInput
from src.app.customfields.services.customFieldService import CustomFieldService
from src.app.database import SessionLocal, get_db
from src.app.groups.models.database.models import Group, GroupCategory, GroupMembership, GroupRole
from src.app.groups.services.groupService import GroupService
from src.app.imports.models.bundle import ImportBundle
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.database.models import Address, Household, PeopleCategory, Person
from src.app.people.models.people import CreatePerson
from src.app.people.personFields import PROFILE_PERSON_FIELDS
from src.app.people.services.addressParts import normalize_address


class ImportService:
    """Idempotent import keyed by source + entity type + external id.

    Importing the same payload twice updates the original rows instead of
    creating duplicates. Unknown source fields are kept on the external reference.
    """

    def __init__(self, db: SessionLocal = Depends(get_db), import_dao: ImportDAO = Depends(ImportDAO),
                 people_factory: PeopleFactory = Depends(PeopleFactory),
                 custom_field_service: CustomFieldService = Depends(CustomFieldService),
                 group_service: GroupService = Depends(GroupService)):
        self.db = db
        self.import_dao = import_dao
        self.people_factory = people_factory
        self.custom_field_service = custom_field_service
        self.group_service = group_service

    def import_bundle(self, bundle: ImportBundle):
        source = bundle.source or "elvanto"
        summary = {
            "people": self._each(source, "person", bundle.people, self._upsert_person),
            "categories": self._each(source, "category", bundle.categories, self._upsert_category),
            "custom_fields": self._each(source, "custom_field", bundle.custom_fields, self._upsert_custom_field),
            "households": self._each(source, "household", bundle.households, self._upsert_household),
            "groups": self._each(source, "group", bundle.groups, self._upsert_group),
            "memberships": self._each(source, "group_membership", bundle.memberships, self._upsert_membership),
            "custom_field_values": self._each(source, "custom_field_value", bundle.custom_field_values, self._upsert_custom_value),
        }
        return summary

    def errors(self, source=None):
        return [
            {
                "id": row.id,
                "source": row.source,
                "entity_type": row.entity_type,
                "external_id": row.external_id,
                "message": row.message,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in self.import_dao.list_errors(source)
        ]

    def _each(self, source, entity_type, records, handler):
        created = updated = 0
        errors = []
        for record in records:
            external_id = getattr(record, "external_id", None)
            try:
                action = handler(source, record)
                self.db.commit()
                if action == "created":
                    created += 1
                else:
                    updated += 1
            except Exception as exc:
                self.db.rollback()
                message = str(exc)
                self.import_dao.add_error(source, entity_type, external_id, message, self._raw(record))
                errors.append({"external_id": external_id, "message": message})
        return {"created": created, "updated": updated, "errors": errors}

    def _upsert_person(self, source, record):
        if not any([record.first_name, record.last_name, record.preferred_name]):
            raise ValueError("A person import needs a name")
        ref = self.import_dao.get_reference(source, "person", record.external_id)
        if ref:
            person = self.db.get(Person, ref.entity_id)
            if person is None:
                raise ValueError("Stored person reference no longer exists")
            self._assign_person(person, record)
            self.import_dao.save_reference(source, "person", person.id, record.external_id, self._raw(record))
            return "updated"
        created = self.people_factory.create_person_entity_from_create_person(CreatePerson(
            first_name=record.first_name,
            last_name=record.last_name,
            preferred_name=record.preferred_name,
            email=record.email,
            mobile_number=record.mobile_number,
            gender=record.gender,
            marital_status=record.marital_status,
        ))
        self._assign_person(created, record)
        self.db.add(created)
        self.db.flush()
        self.import_dao.save_reference(source, "person", created.id, record.external_id, self._raw(record))
        return "created"

    def _assign_person(self, person, record):
        for name in ("first_name", "last_name", "email", "mobile_number", "gender", "marital_status", *PROFILE_PERSON_FIELDS):
            value = getattr(record, name, None)
            if value not in (None, ""):
                if name in {"date_of_birth", "marriage_date", "member_since"} and isinstance(value, str):
                    value = datetime.date.fromisoformat(value[:10])
                setattr(person, name, value)
        if record.date_of_birth:
            person.date_of_birth = datetime.date.fromisoformat(record.date_of_birth[:10])
        if record.marriage_date:
            person.marriage_date = datetime.date.fromisoformat(record.marriage_date[:10])

    def _upsert_category(self, source, record):
        ref = self.import_dao.get_reference(source, f"{record.kind}_category", record.external_id)
        if record.kind == "group":
            model = GroupCategory
            entity_type = "group_category"
        else:
            model = PeopleCategory
            entity_type = "person_category"
        if ref:
            category = self.db.get(model, ref.entity_id)
            category.name = record.name
            category.description = record.description
            category.colour = record.colour
            self.import_dao.save_reference(source, entity_type, category.id, record.external_id, self._raw(record))
            return "updated"
        category = model(name=record.name, description=record.description, colour=record.colour, active=True)
        self.db.add(category)
        self.db.flush()
        self.import_dao.save_reference(source, entity_type, category.id, record.external_id, self._raw(record))
        return "created"

    def _upsert_custom_field(self, source, record):
        ref = self.import_dao.get_reference(source, "custom_field", record.external_id)
        if ref:
            field = self.db.get(CustomFieldDefinition, ref.entity_id)
            field.name = record.name
            field.field_type = record.field_type
            field.description = record.description
            field.required = record.required
            self.import_dao.save_reference(source, "custom_field", field.id, record.external_id, self._raw(record))
            return "updated"
        field = CustomFieldDefinition(
            name=record.name,
            field_type=record.field_type,
            entity_type=record.entity_type,
            description=record.description,
            required=record.required,
            active=True,
        )
        for index, option in enumerate(record.options):
            field.options.append(CustomFieldOption(value=option, label=option, display_order=index, active=True))
        self.db.add(field)
        self.db.flush()
        self.import_dao.save_reference(source, "custom_field", field.id, record.external_id, self._raw(record))
        return "created"

    def _upsert_household(self, source, record):
        leader = self._require_person(source, record.leader_external_id)
        members = [self._require_person(source, external_id) for external_id in record.member_external_ids]
        if leader not in members:
            members.append(leader)
        ref = self.import_dao.get_reference(source, "household", record.external_id)
        if ref:
            household = self.db.get(Household, ref.entity_id)
            household.name = record.name or household.name
            household.notes = record.notes
            household.leader_id = leader.id
            household.people = members
            if record.address:
                self._apply_imported_address(household, record.address)
            self.import_dao.save_reference(source, "household", household.id, record.external_id, self._raw(record))
            return "updated"
        if not record.address:
            raise ValueError("A new household import needs an address")
        address = self._address_from_import(record.address)
        self.db.add(address)
        self.db.flush()
        household = Household(name=record.name, notes=record.notes, leader_id=leader.id, address_id=address.id, people=members)
        self.db.add(household)
        self.db.flush()
        self.import_dao.save_reference(source, "household", household.id, record.external_id, self._raw(record))
        return "created"

    def _address_from_import(self, raw):
        return Address(**normalize_address(raw))

    def _apply_imported_address(self, household, raw):
        parts = normalize_address(raw)
        if household.address is None:
            address = Address(**parts)
            self.db.add(address)
            self.db.flush()
            household.address_id = address.id
            return
        for key, value in parts.items():
            if key in ("latitude", "longitude") and value is None:
                continue
            setattr(household.address, key, value)

    def _upsert_group(self, source, record):
        category_id = None
        if record.category_external_id:
            category_ref = self.import_dao.get_reference(source, "group_category", record.category_external_id)
            if category_ref is None:
                raise ValueError(f"Unknown group category {record.category_external_id}")
            category_id = category_ref.entity_id
        ref = self.import_dao.get_reference(source, "group", record.external_id)
        if ref:
            group = self.db.get(Group, ref.entity_id)
            group.name = record.name
            group.description = record.description
            group.category_id = category_id
            group.status = record.status
            self.import_dao.save_reference(source, "group", group.id, record.external_id, self._raw(record))
            return "updated"
        group = Group(
            name=record.name,
            description=record.description,
            category_id=category_id,
            status=record.status or "active",
        )
        self.db.add(group)
        self.db.flush()
        self.import_dao.save_reference(source, "group", group.id, record.external_id, self._raw(record))
        return "created"

    def _upsert_membership(self, source, record):
        person = self._require_person(source, record.person_external_id)
        group_ref = self.import_dao.get_reference(source, "group", record.group_external_id)
        if group_ref is None:
            raise ValueError(f"Unknown group {record.group_external_id}")
        external_id = f"{record.group_external_id}:{record.person_external_id}"
        role = self.db.query(GroupRole).filter(GroupRole.name == (record.role_name or "Member")).first()
        if role is None:
            role = GroupRole(name=record.role_name or "Member", is_leader=(record.role_name == "Leader"), active=True)
            self.db.add(role)
            self.db.flush()
        ref = self.import_dao.get_reference(source, "group_membership", external_id)
        if ref:
            membership = self.db.get(GroupMembership, ref.entity_id)
            membership.role_id = role.id
            membership.status = record.status
            self.import_dao.save_reference(source, "group_membership", membership.id, external_id, self._raw(record))
            return "updated"
        existing = (
            self.db.query(GroupMembership)
            .filter(GroupMembership.group_id == group_ref.entity_id, GroupMembership.person_id == person.id)
            .first()
        )
        if existing:
            existing.role_id = role.id
            existing.status = record.status
            self.import_dao.save_reference(source, "group_membership", existing.id, external_id, self._raw(record))
            return "updated"
        membership = GroupMembership(
            group_id=group_ref.entity_id,
            person_id=person.id,
            role_id=role.id,
            status=record.status or "active",
            date_joined=datetime.date.today(),
        )
        self.db.add(membership)
        self.db.flush()
        self.import_dao.save_reference(source, "group_membership", membership.id, external_id, self._raw(record))
        return "created"

    def _upsert_custom_value(self, source, record):
        person = self._require_person(source, record.person_external_id)
        field_ref = self.import_dao.get_reference(source, "custom_field", record.field_external_id)
        if field_ref is None:
            raise ValueError(f"Unknown custom field {record.field_external_id}")
        external_id = f"{record.person_external_id}:{record.field_external_id}"
        existed = self.import_dao.get_reference(source, "custom_field_value", external_id) is not None
        self.custom_field_service.set_values("person", person.id, [CustomFieldValueInput(field_id=field_ref.entity_id, value=record.value)])
        value_rows = self.custom_field_service.dao.values_for_entity("person", person.id)
        match = next((row for row in value_rows if row.field_id == field_ref.entity_id), None)
        if match is not None:
            self.import_dao.save_reference(source, "custom_field_value", match.id, external_id, self._raw(record))
        return "updated" if existed else "created"

    def _require_person(self, source, external_id):
        ref = self.import_dao.get_reference(source, "person", external_id)
        if ref is None:
            raise ValueError(f"Unknown person {external_id}")
        person = self.db.get(Person, ref.entity_id)
        if person is None:
            raise ValueError(f"Unknown person {external_id}")
        return person

    def _raw(self, record):
        data = record.model_dump()
        extra = record.model_extra or {}
        data.update(extra)
        return data
