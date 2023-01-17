from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from src.app.database import Base
from sqlalchemy.orm import relationship

class Church(Base):
    __tablename__ = 'church'
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    website = Column(String)
    email = Column(String)
    phone = Column(String)
    logo_image_id = Column(Integer, ForeignKey('images.id'))
    address_id = Column(Integer, ForeignKey('addresses.id'))
    name = Column(String)
    description = Column(String)
    logo_image = relationship("Image", backref="church")
    address = relationship("Address", backref="church")
    #add social media links as well
