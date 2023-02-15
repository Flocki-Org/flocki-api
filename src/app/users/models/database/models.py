from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

from src.app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    mobile_number = Column(String)
    password = Column(String)
    person_id = Column(Integer, ForeignKey('people.id'))
    __table_args__ = (UniqueConstraint('email', name='users_uc'), UniqueConstraint('person_id', name='person_id_uc'))
