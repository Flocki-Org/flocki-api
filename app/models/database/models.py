from sqlalchemy import Column, Integer, String, Date
from ...database import Base

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

#   social_media_links: List[Social  MediaLink] = Field(None, title="A list of social media URLs")