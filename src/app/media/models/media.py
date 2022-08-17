from pydantic import HttpUrl, BaseModel
import datetime

class CreateImage(BaseModel):
    id: int = None
    created: datetime.datetime
    store: str
    address: str
    filename: str = None
    description: str = None
    content_type: str = None
    tags: str = None

class ViewImage(BaseModel):
    id: int = None
    created: datetime.datetime = None
    description: str = None
    tags: str = None