from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship

from src.app.database import Base

class MediaItem(Base):
    __tablename__ = 'media_items'
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    store = Column(String, nullable=False)
    address = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    description = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    tags = Column(String, nullable=True)    # comma separated list of tags


