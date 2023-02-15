from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey, DECIMAL, DateTime, Table, TIMESTAMP
from src.app.database import Base
from sqlalchemy.orm import relationship

HouseholdPerson = Table('household_people', Base.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('created', TIMESTAMP, default=datetime.utcnow, nullable=False),
                        Column('household_id', Integer, ForeignKey('households.id'), nullable=False),
                        Column('person_id', Integer, ForeignKey('people.id'), nullable=False))


class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    mobile_number = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    marriage_date = Column(Date)
    marital_status = Column(String)
    registered_date = Column(Date)
    social_media_links = relationship("SocialMediaLink", cascade="all, delete-orphan")
    addresses = relationship("PeopleAddress", back_populates="person", cascade="all, delete-orphan")
    households = relationship("Household", secondary=HouseholdPerson, viewonly=True)  # , cascade="all, delete-orphan")
    profile_images = relationship("PersonImage", back_populates="person", cascade="all, delete-orphan")
    #as list false
    user = relationship("User", backref="person", uselist=False)

class SocialMediaLink(Base):
    __tablename__ = 'social_media_links'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    type = Column(String)
    url = Column(String)
    _table_args__ = (UniqueConstraint('person_id', 'type', name='socialmedialinks_person_type_uc'),)


class PeopleAddress(Base):
    __tablename__ = 'people_addresses'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    person = relationship("Person", back_populates="addresses")
    address = relationship("Address")
    _table_args__ = (UniqueConstraint('person_id', 'address_id', name='peopleaddresses_person_address_uc'))


class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    building = Column(String)
    streetNumber = Column(String)
    street = Column(String)
    complex = Column(String)
    suburb = Column(String)
    city = Column(String)
    province = Column(String)
    country = Column(String)
    postalCode = Column(String)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    _table_args__ = (UniqueConstraint('person_id', 'type', name='addresses_person_type_uc'),
                     UniqueConstraint('household_id', name='addresses_household_uc'))


class Household(Base):
    __tablename__ = 'households'
    id = Column(Integer, primary_key=True, index=True)
    leader_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    address = relationship("Address", cascade=None)
    household_images = relationship("HouseholdImage", back_populates="household", cascade="all, delete-orphan")
    leader = relationship("Person", cascade=None, foreign_keys=[leader_id])
    people = relationship(Person, secondary=HouseholdPerson)  # , primaryjoin="Household.id == HouseholdPerson.household_id")


class PersonImage(Base):
    __tablename__ = 'people_images'
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    person = relationship("Person", back_populates="profile_images")
    image = relationship("Image")
    # __table_args__ = (UniqueConstraint('person_id', 'image_id', name='peopleimages_person_image_uc'),)


class HouseholdImage(Base):
    __tablename__ = 'household_images'
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    household_id = Column(Integer, ForeignKey('households.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    household = relationship("Household", back_populates="household_images")
    image = relationship("Image")
