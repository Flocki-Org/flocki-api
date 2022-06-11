from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey, false
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

class SocialMediaLinks(Base):
    __tablename__ = 'social_media_links'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=false)
    type = Column(String)
    url = Column(String)
    person = relationship("Person", back_populates='social_media_links')
    _table_args__ = (UniqueConstraint('person_id', 'type', name='socialmedialinks_person_type_uc'),)
#   social_media_links: List[Social  MediaLink] = Field(None, title="A list of social media URLs")