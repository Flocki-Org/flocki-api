from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    DECIMAL,
    TIMESTAMP,
    Table,
    Text,
)
from sqlalchemy.orm import backref, relationship

from src.app.database import Base


def _naive_utcnow():
    # Same naive UTC timestamp datetime.utcnow() returned. utcnow() is deprecated on Python 3.15.
    return datetime.now(UTC).replace(tzinfo=None)


HouseholdPerson = Table(
    "household_people",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("created", TIMESTAMP, default=_naive_utcnow, nullable=False),
    Column("household_id", Integer, ForeignKey("households.id"), nullable=False),
    Column("person_id", Integer, ForeignKey("people.id"), nullable=False),
)

Index("ix_household_people_household", HouseholdPerson.c.household_id)
Index("ix_household_people_person", HouseholdPerson.c.person_id)


class Person(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    preferred_name = Column(String)
    middle_name = Column(String)
    title = Column(String)
    email = Column(String)
    mobile_number = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    marriage_date = Column(Date)
    marital_status = Column(String)
    registered_date = Column(Date)
    biography = Column(Text)
    preferred_contact_method = Column(String)
    contact_preferences = Column(Text)
    membership_status = Column(String)
    member_since = Column(Date)
    date_first_attended = Column(Date)
    baptism_status = Column(String)
    baptism_date = Column(Date)
    baptism_location = Column(String)
    confirmation_date = Column(Date)
    previous_church = Column(String)
    membership_transfer_notes = Column(Text)
    date_joined = Column(Date)
    date_membership_ended = Column(Date)
    reason_for_leaving = Column(Text)
    ministry_involvement = Column(Text)
    pastoral_notes = Column(Text)
    lifecycle_status = Column(String)
    archived_at = Column(DateTime)
    school_grade = Column(String)
    school_name = Column(String)
    occupation = Column(String)
    employer = Column(String)
    nationality = Column(String)
    preferred_language = Column(String)
    timezone = Column(String)
    volunteer_status = Column(String)
    skills = Column(Text)
    interests = Column(Text)
    allergies = Column(Text)
    special_requirements = Column(Text)
    emergency_notes = Column(Text)
    external_image_url = Column(String)
    created_at = Column(DateTime, default=_naive_utcnow)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow)
    social_media_links = relationship("SocialMediaLink", cascade="all, delete-orphan")
    addresses = relationship("PeopleAddress", back_populates="person", cascade="all, delete-orphan")
    households = relationship("Household", secondary=HouseholdPerson, viewonly=True)
    profile_images = relationship("PersonImage", back_populates="person", cascade="all, delete-orphan")
    user = relationship("User", backref="person", uselist=False)

    __table_args__ = (
        Index("ix_people_last_first", "last_name", "first_name"),
        Index("ix_people_email", "email"),
        Index("ix_people_mobile", "mobile_number"),
        Index("ix_people_preferred_name", "preferred_name"),
        Index("ix_people_lifecycle", "lifecycle_status"),
        Index("ix_people_membership_status", "membership_status"),
        Index("ix_people_dob", "date_of_birth"),
        Index("ix_people_gender", "gender"),
        Index("ix_people_marital_status", "marital_status"),
    )


class SocialMediaLink(Base):
    __tablename__ = "social_media_links"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    type = Column(String)
    url = Column(String)
    # Historical typo: this is not __table_args__, so the constraint is not applied.
    _table_args__ = (("person_id", "type"),)


class PersonEmail(Base):
    __tablename__ = "person_emails"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    email = Column(String, nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    label = Column(String)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    person = relationship("Person", backref=backref("emails", cascade="all, delete-orphan"))
    __table_args__ = (
        Index("ux_person_emails_person_email", "person_id", "email", unique=True),
        Index("ix_person_emails_email", "email"),
    )


class PersonPhone(Base):
    __tablename__ = "person_phones"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    number = Column(String, nullable=False)
    phone_type = Column(String, nullable=False, default="mobile")
    is_primary = Column(Boolean, nullable=False, default=False)
    label = Column(String)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    person = relationship("Person", backref=backref("phones", cascade="all, delete-orphan"))
    __table_args__ = (
        Index("ix_person_phones_person", "person_id"),
        Index("ix_person_phones_number", "number"),
    )


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    name = Column(String, nullable=False)
    relationship_label = Column(String)
    phone = Column(String)
    email = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    person = relationship("Person", backref=backref("emergency_contacts", cascade="all, delete-orphan"))
    __table_args__ = (Index("ix_emergency_contacts_person", "person_id"),)


class PersonRelationship(Base):
    __tablename__ = "person_relationships"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    related_person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    relationship_type = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    person = relationship(
        "Person",
        foreign_keys=[person_id],
        backref=backref("relationships_out", cascade="all, delete-orphan"),
    )
    related_person = relationship("Person", foreign_keys=[related_person_id])
    __table_args__ = (
        CheckConstraint("person_id <> related_person_id", name="ck_relationship_not_self"),
        Index(
            "ux_person_relationship",
            "person_id",
            "related_person_id",
            "relationship_type",
            unique=True,
        ),
        Index("ix_person_relationship_related", "related_person_id"),
    )


class PeopleCategory(Base):
    __tablename__ = "people_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    colour = Column(String)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_people_categories_name", "name", unique=True),)


class PersonCategoryLink(Base):
    __tablename__ = "person_category_links"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("people_categories.id"), nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    person = relationship("Person", backref=backref("category_links", cascade="all, delete-orphan"))
    category = relationship("PeopleCategory")
    __table_args__ = (
        Index("ux_person_category", "person_id", "category_id", unique=True),
        Index("ix_person_category_category", "category_id"),
    )


class PersonStatusHistory(Base):
    __tablename__ = "person_status_history"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    field_name = Column(String, nullable=False)
    previous_value = Column(String)
    new_value = Column(String)
    reason = Column(Text)
    changed_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    changed_by_user_id = Column(Integer)
    person = relationship("Person", backref=backref("status_history", cascade="all, delete-orphan"))
    __table_args__ = (Index("ix_person_status_history_person", "person_id", "changed_at"),)


class ServiceType(Base):
    __tablename__ = "service_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_service_types_name", "name", unique=True),)


class PersonServiceType(Base):
    __tablename__ = "person_service_types"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    person = relationship("Person", backref=backref("service_type_links", cascade="all, delete-orphan"))
    service_type = relationship("ServiceType")
    __table_args__ = (
        Index("ux_person_service_type", "person_id", "service_type_id", unique=True),
    )


class ReferenceValue(Base):
    __tablename__ = "reference_values"
    id = Column(Integer, primary_key=True)
    domain = Column(String, nullable=False)
    value = Column(String, nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_reference_domain_value", "domain", "value", unique=True),)


class PeopleAddress(Base):
    __tablename__ = "people_addresses"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    is_primary = Column(Boolean, nullable=True, default=False)
    person = relationship("Person", back_populates="addresses")
    address = relationship("Address")
    # Historical typo kept so an invalid UniqueConstraint is not switched on.
    _table_args__ = (("person_id", "address_id"),)
    __table_args__ = (
        Index("ix_people_addresses_person_address", "person_id", "address_id"),
        Index("ix_people_addresses_address", "address_id"),
    )


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    building = Column(String)
    unit = Column(String)
    street_number = Column(String)
    street = Column(String)
    complex = Column(String)
    suburb = Column(String)
    city = Column(String)
    province = Column(String)
    country = Column(String)
    postal_code = Column(String)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    # Historical typo kept. The original constraint referenced columns this table does not have.
    _table_args__ = (("type",),)
    __table_args__ = (
        Index("ix_addresses_city_suburb", "city", "suburb"),
        Index("ix_addresses_postal_code", "postal_code"),
    )


class Household(Base):
    __tablename__ = "households"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    notes = Column(Text)
    leader_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow)
    address = relationship("Address", cascade=None)
    household_images = relationship("HouseholdImage", back_populates="household", cascade="all, delete-orphan")
    leader = relationship("Person", cascade=None, foreign_keys=[leader_id])
    people = relationship(Person, secondary=HouseholdPerson)
    __table_args__ = (Index("ix_households_leader", "leader_id"),)


class PersonImage(Base):
    __tablename__ = "people_images"
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("media_items.id"), nullable=False)
    person = relationship("Person", back_populates="profile_images")
    image = relationship("MediaItem")


class HouseholdImage(Base):
    __tablename__ = "household_images"
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("media_items.id"), nullable=False)
    household = relationship("Household", back_populates="household_images")
    image = relationship("MediaItem")


# Register related mapped classes before the first query configures mappers.
from src.app.media.models.database.models import MediaItem  # noqa: E402,F401
from src.app.users.models.database.models import User  # noqa: E402,F401
