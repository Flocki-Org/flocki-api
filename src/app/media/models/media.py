from typing import Optional

from pydantic import BaseModel
import datetime

class CreateMediaItem(BaseModel):
    id: Optional[int] = None
    created: datetime.datetime
    store: str
    address: str
    filename: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[str] = None
    tags: Optional[str] = None

class ViewMediaItem(BaseModel):
    id: Optional[int] = None
    created: Optional[datetime.datetime] = None
    description: Optional[str] = None
    tags: Optional[str] = None
