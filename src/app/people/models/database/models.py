from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey, false, DECIMAL
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
    social_media_links = relationship("SocialMediaLinks", back_populates='person', cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates='person', cascade="all, delete-orphan")


class SocialMediaLinks(Base):
    __tablename__ = 'social_media_links'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=false)
    type = Column(String)
    url = Column(String)
    person = relationship("Person", back_populates='social_media_links')
    _table_args__ = (UniqueConstraint('person_id', 'type', name='socialmedialinks_person_type_uc'),)

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=false)
    type = Column(String)
    streetNumber = Column(String)
    street = Column(String)
    suburb = Column(String)
    city = Column(String)
    province = Column(String)
    country = Column(String)
    postalCode = Column(String)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    person = relationship("Person", back_populates='addresses')
    _table_args__ = (UniqueConstraint('person_id', 'type', name='addresses_person_type_uc'),)
