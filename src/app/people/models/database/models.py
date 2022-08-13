from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey, DECIMAL, DateTime
from src.app.database import Base
from sqlalchemy.orm import relationship

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
    household_id = Column(Integer, ForeignKey('households.id'), nullable=True)
    social_media_links = relationship("SocialMediaLink", cascade="all, delete-orphan")
    addresses = relationship("PeopleAddress", back_populates="person", cascade="all, delete-orphan")
    household = relationship("Household", back_populates="people", foreign_keys=[household_id])
    profile_images = relationship("PersonImage", back_populates="person", cascade="all, delete-orphan")

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
    _table_args__ = (UniqueConstraint('person_id', 'type', name='addresses_person_type_uc'), UniqueConstraint('household_id', name='addresses_household_uc'))

class Household(Base):
    __tablename__ = 'households'
    id = Column(Integer, primary_key=True, index=True)
    leader_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    address = relationship("Address", cascade=None)
    leader = relationship("Person", cascade=None, foreign_keys=[leader_id])
    people = relationship("Person", back_populates="household", primaryjoin="Household.id == Person.household_id")

class PersonImage(Base):
    __tablename__ = 'people_images'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    created = Column(DateTime, nullable=False)
    person = relationship("Person", back_populates="profile_images")
    image = relationship("Image")
    #__table_args__ = (UniqueConstraint('person_id', 'image_id', name='peopleimages_person_image_uc'),)