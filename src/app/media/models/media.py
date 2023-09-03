from pydantic import HttpUrl, BaseModel
import datetime

class CreateMediaItem(BaseModel):
    id: int = None
    created: datetime.datetime
    store: str
    address: str
    filename: str = None
    description: str = None
    content_type: str = None
    tags: str = None

class ViewMediaItem(BaseModel):
    id: int = None
    created: datetime.datetime = None
    description: str = None
    tags: str = None